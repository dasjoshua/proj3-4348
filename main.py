import os 
import struct

def create():
    
    filename = input("Enter filename to create: ").strip()

    # Check if we need to overwrite
    if os.path.exists(filename):
        overwrite = input("File exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("Operation aborted. File not created.")
            return None

    
    try:
        with open(filename, "wb") as file:
            # Initialize first block for the header
            MAGIC_NUMBER = b"4337PRJ3"
            if len(MAGIC_NUMBER) < 8: # ensure magic number is 8 bytes
                MAGIC_NUMBER += b'\x00' * (8 - len(MAGIC_NUMBER))  # Pad with null bytes

            root_block_id = (0).to_bytes(8, "big")
            next_block_id = (1).to_bytes(8, "big")
            unused_space = bytes(512 -  (len(MAGIC_NUMBER) + len(root_block_id) + len(next_block_id)) )
            file.write(MAGIC_NUMBER + root_block_id + next_block_id + unused_space)

        print(f"File '{filename}' successfully created and initialized.")
        return filename 
    
    except Exception as e:
        print(f"Error creating file: {e}")
        return None
# -----  END OF CREATE FUNCTION -----------------------------------------------------------------------------

def open_file():
    
    filename = input("Enter the filename to open: ").strip()

    # Check if the file exists
    if not os.path.exists(filename):
        print("Error: File does not exist.")
        return None

    try:
        with open(filename, "rb") as file:
            # Read the first 8 bytes for the magic number
            magic_number = file.read(8)

            # Validate the magic number
            if magic_number != b"4337PRJ3".ljust(8, b'\x00'):  # Ensure it's 8 bytes long
                print("Error: Invalid file format.")
                return None

        print(f"File '{filename}' successfully opened.")
        return filename  # Return the file name to update the open file state
    except Exception as e:
        print(f"Error opening file: {e}")
        return None
# ------------------ END OF OPEN FUNCTION ----------------------------------------------------------

def insert(open_file, key, value):

    try:

        # Open the file in read/write mode
        with open(open_file, "rb+") as file:
            # Read the header to find the root block
            file.seek(0)
            header = file.read(24)  # 8 bytes magic, 8 bytes root_block_id, 8 bytes next_block_id
            magic_number, root_block_id, next_block_id = struct.unpack(">8sQQ", header)

            # If this is the first value being inserted, create a root node
            if root_block_id == 0:
                root_block_id = next_block_id
                next_block_id += 1

                # Write the new root node
                root_node = create_btree_node(root_block_id, 0, [(key, value)])
                file.seek(root_block_id * 512)
                file.write(root_node)

                # Update the header
                file.seek(8)
                file.write(struct.pack(">QQ", root_block_id, next_block_id))

                print(f"Inserted ({key}, {value}) as the first entry in the tree.")
                return

            current_block_id = root_block_id
            while True:
                # Read the current node
                file.seek(current_block_id * 512)
                node_data = file.read(512)
                
                # Unpack node information
                fixed_data = node_data[:488] # skip the 24 unused bytes at the end 
                node_format = ">QQQ" + "Q" * 19 + "Q" * 19 + "Q" * 20
                block_id, parent_block_id, num_keys, *rest = struct.unpack(node_format, fixed_data)
                
                # Split the rest into keys, values, and children
                keys = rest[:19]
                values = rest[19:38]
                children = rest[38:]

                # Check if this is a leaf node (no children)
                is_leaf = all(child == 0 for child in children)

                if is_leaf:
                    # Check if key already exists
                    if key in keys[:num_keys]:
                        print(f"Error: Key {key} already exists.")
                        return

                    # If the node is not full, insert the key
                    if num_keys < 19:
                        # insert key at the next available key location
                        insert_pos = 0
                        while insert_pos < num_keys and keys[insert_pos] < key:
                            insert_pos += 1


                        # Insert the new key and value
                        keys[insert_pos] = key
                        values[insert_pos] = value
                        
                        # Update the number of keys
                        num_keys += 1

                        # save the node
                        updated_node = struct.pack(node_format, 
                            block_id, parent_block_id, num_keys, 
                            *keys, *values, *children)

                        # Write the updated node back to file
                        file.seek(current_block_id * 512)
                        file.write(updated_node)

                        print(f"Inserted ({key}, {value}) into the tree.")
                        return

                        # If node is full, we need to split
                    else:
                        # Perform node split
                        split_result = split_node(file, current_block_id, next_block_id)
                        if not split_result:
                            print("Error during node split.")
                            return
                        
                        next_block_id, middle_key, middle_value, new_node_block_id = split_result

                        # If root is being split
                        if current_block_id == root_block_id:
                            # Create a new root
                            new_root_block_id = next_block_id
                            next_block_id += 1

                            # Create new root node with median key
                            new_root_node = create_btree_node(
                                new_root_block_id, 
                                0, 
                                [(middle_key, middle_value)]
                            )

                            # Update root node's children
                            file.seek(new_root_block_id * 512 + 488)  # Go to children section
                            file.write(struct.pack(">QQ", current_block_id, new_node_block_id))

                            # Write new root node
                            file.seek(new_root_block_id * 512)
                            file.write(new_root_node)

                            # Update header with new root and next block ID
                            file.seek(8)
                            file.write(struct.pack(">QQ", new_root_block_id, next_block_id))

                            print(f"Root split. New root contains ({middle_key}, {middle_value})")
                            return

                        # For non-root splits, we need to insert median into parent
                        else:
                            # Need to implement parent node insertion logic here
                            # This would involve recursively splitting parent nodes if needed
                            print("Parent node insertion not fully implemented.")
                            return

                # If not a leaf, find the appropriate child to descend into
                else:
                    # Find the correct child pointer
                    child_index = 0
                    while child_index < num_keys and keys[child_index] < key:
                        child_index += 1
                    
                    # Update tracking variables
                    parent_block_id = current_block_id
                    current_block_id = children[child_index]

    except Exception as e:
        print(f"Error during insert operation: {e}")

def create_btree_node(block_id, parent_id, key_value_pairs):
    
    
    # initialize space for keys + values
    keys = [0] * 19
    for i, (key, _) in enumerate(key_value_pairs):
        keys[i] = key
    
    values = [0] * 19
    for i, (_, value) in enumerate(key_value_pairs):
        values[i] = value
    
   
    offset = [0] * 20
    
    # Node format:
    # 8-bytes block id
    # 8-bytes parent block id
    # 8-bytes number of keys
    # 152-bytes for keys (19 * 8 bytes)
    # 152-bytes for values (19 * 8 bytes)
    # 160-bytes for children (20 * 8 bytes)
    node_format = ">QQQ" + "Q" * 19 + "Q" * 19 + "Q" * 20
    
    # Pack the node data
    node_data = struct.pack(node_format, 
        block_id, 
        parent_id, 
        len(key_value_pairs), 
        *keys,    
        *values,    
        *offset     
    )
    
    
    return node_data

def split_node(file, current_block_id, next_block_id):

    try:
        # Read the full node
        file.seek(current_block_id * 512)
        node_data = file.read(512)
        
        # Unpack the node
        node_format = ">QQQ" + "Q" * 19 + "Q" * 19 + "Q" * 20
        unpacked = struct.unpack(node_format, node_data[:488])
        
        block_id, parent_block_id, num_keys = unpacked[:3]
        keys = list(unpacked[3:22])
        values = list(unpacked[22:41])
        children = list(unpacked[41:61])
        
        # B-tree nodes are split by finding the middle value and making the left half the left child, and the right half the right child

        # so first will save variables for the middle, left half and right half. And those halves will both become seperate new nodes

        middle_index = 9
        
        middle_key = keys[middle_index]
        middle_value = values[middle_index]
        
        # save left node data 
        left_keys = keys[:middle_index] + [0] * (19 - len(keys[:middle_index]))
        left_values = values[:middle_index] + [0] * (19 - len(values[:middle_index]))
        left_children = children[:middle_index + 1] + [0] * (20 - len(children[:middle_index + 1]))
        
        # save right node data
        right_keys = keys[middle_index + 1:] + [0] * (19 - len(keys[middle_index + 1:]))
        right_values = values[middle_index + 1:] + [0] * (19 - len(values[middle_index + 1:]))
        right_children = children[middle_index + 1:] + [0] * (20 - len(children[middle_index + 1:]))
        
        
        # Create left node
        left_node_data = struct.pack(node_format, 
            current_block_id,  # Keep the original block ID for the left node
            parent_block_id,   # Keep the original parent
            len(keys[:middle_index]),    # Number of keys
            *left_keys, 
            *left_values, 
            *left_children
        )
        
        # Create right node
        right_node_block_id = next_block_id
        next_block_id += 1
        
        right_node_data = struct.pack(node_format,
            right_node_block_id,  # New block ID for right node
            parent_block_id,       # Keep the original parent
            len(keys[middle_index + 1:]),       # Number of keys
            *right_keys,
            *right_values,
            *right_children
        )

        # Write to file
        file.seek(current_block_id * 512)
        file.write(left_node_data)
        
       
        file.seek(right_node_block_id * 512)
        file.write(right_node_data)
        
        return next_block_id, middle_key, middle_value, right_node_block_id
    
    except Exception as e:
        print(f"Error during node split: {e}")
        return None

# ---------- END OF INSERT FUNCTION ------------------------------------------------------------------------------

def search(open_file):   
    
    if not open_file:
        print("No index file is open. Please create or open a file first.")
        return

    try:
        search_term = int(input("Enter the key (unsigned integer) to search for: "))

        with open(open_file, "rb") as file:
            # Read the header to find the root block ID
            file.seek(8)  # Skip the magic number
            root_block_id = int.from_bytes(file.read(8), "big")

            if root_block_id == 0:
                print("The B-Tree is empty.")
                return

            
            current_block_id = root_block_id

            while current_block_id != 0:
                
                file.seek(current_block_id * 512)
                node_data = file.read(512)
                node = read_btree_node(node_data)

                # iterate through each key in the node
                for i in range(node["num_keys"]):
                    # search each key for the search term
                    if node["keys"][i] == search_term:
                        print(f"Key: {search_term}, Value: {node['values'][i]}")
                        return

                # Determine which child node to traverse to
                i = 0
                while i < node["num_keys"] and search_term > node["keys"][i]:
                    i += 1

                current_block_id = node["children"][i]  # update to check the next nod

            # key doesn't exist
            print(f"Error: Key {search_term} not found.")
    except Exception as e:
        print(f"Error during search operation: {e}")
# ------------- END OF SEARCH FUNCTION ----------------------------------------------------------------

def load(open_file):
    
    if not open_file:
        print("No index file is open.")
        return

    input_file = input("Enter load file: ").strip()

    # Check if the input file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        return

    try:
        with open(input_file, "r") as file:

            for line in file:
                line_number += 1 # debugging
                # Skip empty lines
                if not line.strip():
                    continue

                list = line.strip().split(',')
                key = int(list[0])
                value = int(list[1])

                # Insert the key-value pair into the B-Tree
                insert(open_file, key, value)


    except Exception as e:
        print(f"Error during load operation: {e}")


def print_btree(open_file):
    
    
    if not open_file:
        print("No index file is open. Please create or open a file first.")
        return

    try:
        with open(open_file, "rb") as file:
            # Read the header to find the root block ID
            file.seek(8)  # Skip magic number
            root_block_id = int.from_bytes(file.read(8), "big")

            if root_block_id == 0:
                print("The B-Tree is empty.")
                return

            # Use a queue for level-order traversal
            queue = [root_block_id]

            print("Key-Value pairs in the B-Tree:")

            while queue:
                current_block_id = queue.pop(0)

                # Read the current node
                file.seek(current_block_id * 512)
                node = read_btree_node(file.read(512))

                # Print all key-value pairs in this node
                for i in range(node["num_keys"]):
                    key = node["keys"][i]
                    value = node["values"][i]
                    print(f"{key}: {value}")

                # Add the rest of the blocks
                queue.extend([child for child in node["children"] if child != 0])

    except Exception as e:
        print(f"Error while printing B-Tree: {e}")

def read_btree_node(data):
   
    node_data = data[:488] # skip the 24 unused bytes at the end 
    node_format = ">QQQ" + "Q" * 19 + "Q" * 19 + "Q" * 20
    unpacked = struct.unpack(node_format, node_data)

    return {
        "block_id": unpacked[0],
        "parent_id": unpacked[1],
        "num_keys": unpacked[2],
        "keys": list(unpacked[3:22]),
        "values": list(unpacked[22:41]),
        "children": list(unpacked[41:61]),
    }
# ----------- END OF PRINT FUNCTION ------------------------------------------------------

def extract(open_file):
   
    if not open_file:
        print("No index file is open. Please create or open a file first.")
        return

    output_file = input("Enter the output filename: ").strip()

    # overwrite logic for output file
    if os.path.exists(output_file):
        overwrite = input(f"File '{output_file}' already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("Command aborted.")
            return

    try:
        with open(open_file, "rb") as file:
            
            file.seek(8)  # Skip the magic number
            root_block_id = int.from_bytes(file.read(8), "big")

            if root_block_id == 0:
                print("The B-Tree is empty. Nothing to extract.")
                return

            # Start traversing the B-Tree
            queue = [root_block_id]
            key_value_pairs = []

            while queue:
                current_block_id = queue.pop(0)

                # Read the current node
                file.seek(current_block_id * 512)
                node_data = file.read(512)
                node = read_btree_node(node_data)

                # Collect key-value pairs from this node
                for i in range(node["num_keys"]):
                    key = node["keys"][i]
                    value = node["values"][i]
                    key_value_pairs.append(f"{key},{value}")

                # Add non-zero child pointers to the queue
                queue.extend([child for child in node["children"] if child != 0])

        # Write the collected key-value pairs to the output file
        with open(output_file, "w") as out_file:
            out_file.write("\n".join(key_value_pairs))
            print(f"Key-value pairs successfully extracted to '{output_file}'.")

    except Exception as e:
        print(f"Error during extraction: {e}")
# --------------------- END OF EXTRACT FUNCTION ------------------------------------------------


def print_menu():
    print("\nCommands:")
    print("create - Create a new index file")
    print("open - Open an existing index file")
    print("insert - Insert a key-value pair")
    print("search - Search for a key")
    print("load - Load key-value pairs from a file")
    print("print - Print all key-value pairs")
    print("extract - Save key-value pairs to a file")
    print("quit - Exit the program")

def main():

    open_filename = None # current working file 

    print_menu()
    while True:
        command = input("Enter command: ").strip().lower()

        if(command == "create"):
            open_filename = create()
        elif(command == "open"):
            open_filename = open_file()
        elif(command == "insert"):
            if not open_file:
                print("No index file is open. Please create or open a file first.")
                continue
    
            key = int(input("Enter key (unsigned integer): "))
            value = int(input("Enter value (unsigned integer): "))
            insert(open_filename, key, value)

        elif(command == "search"):
            search(open_filename)
        elif(command == "load"):
            load(open_filename)
        elif(command == "print"):
            print_btree(open_filename)
        elif(command == "extract"):
            extract(open_filename)
        elif(command == "quit"):
            exit()

if __name__ == "__main__":
    main()
