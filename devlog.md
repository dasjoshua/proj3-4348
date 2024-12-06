-- 11/31 - 3:12pm --
(initially written out on paper and now moving to the devlog)
Putting the project into my own words:

-   the program is meant to be managing creating and doing functions on
    index files. Basically meaning that instead of simply creating files and writing text to it
    I'm needing to allocate ONLY 512 BYTES. And I think I can only put data in certain sections / spaces
    of this total size. Actually I misread it, the file is split up into blocks and there can be as many # of blocks.
    It's just that each block is given a max size of 512 bytes. (and each block will have subdivided sections for data)

-   When new files are made I need to make sure that the first 24 bytes are dedicated to the header. JK it's the first block (512 bytes) are used by the header, but it only uses 24 bytes.
-   first 8 bytes are "4337PRJ3"
-   next 8 bytes are the first node (but after the create command this space will be zero bc there's no root node initialized)
-   last 8 bytes mem location for the next spot the next node can be added to.

-   When nodes are inserted into the file (I'm gonna assume new nodes will be inserted like a complete tree)
-   first 8 bytes are the block's id
-   next 8 bytes is the block id from the parent
-   8 bytes are the total number of key / value pairs
-   then the next 152 bytes are allocated to hold 19 key values
-   next 152 bytes are to hold the 19 possible values
-   then the last 160 bytes will hold the offset (unsure what the offset is but hoping I figure it out later)

Visual representation of the files: 

 _____________________     _______________________________________________________________________    ____________________________________________
|     (512 bytes)      |  |                         (512 bytes)                                   |  |                                            |
|    HEADER BLOCK      |  |                         NODE BLOCK - ROOT                             |  |          FREE NODE BLOCK                   |
|   8 bytes - magic #  |  |     8 bytes block id - 8 bytes parent id - 8 bytes # of key/val pairs |  |                                            |
|   8 bytes - root loc |  |   152 bytes of 64 bit keys - 152 bytes of 64 bit vals                 |  |                                            |
|   8 bytes - next loc |  |           160 bytes of 64 bit offsets (idk)                           |  |  (this location of the next free space     |
|______________________|  |                                                                       |  |   in memory is stored in the header block) |
                          |_______________________________________________________________________|  |____________________________________________|


Initial confusion:

-   So I thought the user was inserting nodes, but actually the user can only insert key value pairs. So it looks like whenever you fill up the 19th pair
    the next pair will need to wait for a new node block to be created, then the pair will be inserted in the new node.

Development plan:

-   First I'll make the menu of commands as that's a simple plug back in from a previous project
    and create user input handling where each command that is written will simply write back the command name to the screen

-   Then after I'll first get started on the creation of the header bits when a new file is being created.

-- 12/2 - 2:20pm --
I was focused on my digital logic exam, and was unable to implement my initial development plan. So will be working tonight to catch up

Plan:

-   Create the menu of commands, and get the create command to make a new file with an initialized header block.

Working remarks:

-   Sweet looks like the menu + create functions work. Now onto the insert and print functions.
-   learned in python that you can allocate null bits by using b"\x00"
    and if you want to store a variable in raw bytes you could simply say b"value"

-   Working on the insert function
-   ran into some issues with tracking if the file is open, so needed to rewrite the create function to also say the file is open  
    Also now running into issues with inserting subsequent pairs using the struct library.
    -> The issue of inserting any new pairs after the first was because I wasn't seeking to the correct point in the file that was empty to add new pairs.
    Rather it would want to insert new pairs at the end of the block, therefore it wasn't allowing any new data to be inserted.

-- 12/2 - 11:12pm --

Plan:

-   now I need to implement the functionality of creating a new node after the root node is fully populated.
    Then I'll create the print function and call it a night.

Working remarks:

-   now running into an issue after creating the new overflow node. New values aren't able to be inserted
    -> I HAVE SPENT 3 HOURS TRYING TO DEBUG THIS ISSUE AND I'M STILL NOT SURE WHAT'S HAPPENING.
    So instead of simply using the to bytes function and seeking to the next pair, I've tried using the struct library
    as that's what stackoverflow said works when inserting at a specific location in a file.
    And I've added a verification step in the insert function to make sure that the block is 512 bytes after a new node has been created.
    but still when inserting a new pair into the next node it says that a buffer is required, and I'm unsure how to resolve it.

-   last thing I'll work on tonigh is the print function and I'll look back at this in the morning.
    -> it took me a really long time to figure out how to iterate on each pair as i first tried using a for loop
    but then I switched to using a while loop based on each block and that was able to atleast print out the first block.
    it would print the first 3 pairs then the program would crash saying that unpack requires a buffer of 488. Hopefully I can figure this out in the morning

-- 12/3 11:22pm --

Plan: Resolve the unpacking issue

-   Reading more into the buffer issue I realized what the error was, and it was because in my node formatter I wasn't accounting for the last 24 bits being unused
    So I made a fix to slice the last unused bits and now the program doesn't run into an exception.

-- 12/4 3:48pm --
Plan: Create the search function

-   Now to work on the search function.
    Luckily my first go at this function ended up working as using python lets you iterate through the list of keys nicely.
    And as there is a max of 19 values I thought it would be ok to do a comparison for each individual key. If i get time later
    I will implement a binary search as I expect the number of nodes to grow, but for now this will work.
-   I went to test the insert again but now whenever a node gets full the program stalls when creating a new node after the root. I am going to figure this out in my next session later tonight

-- 12/4 12:06pm --

Plan: Create the extract function and debug the insert function to stop stalling

-   With the extract function I was able to use the same iterating logic from my search function.
    but instead of checking for a search term I replaced the logic by storing the current pair into a list
    Then after iterating I would dump the list into the desired output file. Able to get it working

-   I tried multiple solutions but nothing seemed to work.
    I re did my previous slicing solution where I stopped saving the 24 unused bits at the end of the block, and instead added padding bits, but the issue persisted
    And I also tried using an enumerate to first initialize the space for key value pairs. But the issue persisted.

-   Also now running into an issue with my git repository saying my test file has exceeded GitHub's filesize limit
    I've tried deleting the file from my local folder, reverting to previous commits, but somehow this file is stuck in the history.
    I'll see if I can fix it tomorrow but I might have to make a new repository.

-- 12/5 4:30pm --
(had an exam today so wasn't able to continue progress until 4:30pm)

- I tried to resolve this issue by stepping back a commit and deleting the file in the folder, but
somehow it's still being cached in the history. So I'm making a new repository. Unfortunately this is getting rid of my previous history, but my devlog still shows it

- To make sure I don't accidently do this again I'm putting all my tests file into a test folder 
 and putting this folder under my gitignore

Hoping that this is still ok because my devlog still proves my previous work, and I don't understand why the file is preventing me from pushing to my previous repository.

-- 12/5 4:35pm -- 

Plan: create the load function

 - will be assuming that the values come in the form 
 'n,n\n' 
 While writing I realized I could reuse the previous insert function if I were to rewrite it.
 So I moved the user input that was originally in the insert function into main, so that I could reuse it for my load function
 
 - Ran into an issue that took me an hour to figure out, in main I accidently wrote the parameter as 'open_file' instead of 'open_filename'
 and this resulted in the load function reading the filename as a function and the program would error out. 
 I thought it was an issue in how I was parsing the numbers in the file, and tried multiple solutions until I realized I had a typo. 

-- 12/5 5:52pm -- 

Plan: try to debug the error with creating new nodes

 - I realize now I initially misunderstood the splitting functionality for a B-tree 
 whenever a node is full, the current node gets split into two and the middle value gets pushed up as the root. 

 - after watching a video about B-trees I updated the logic and am now instead of just making a single new node and putting the overflow pairs in it 
 I'm splitting the node into a left and right node. 

 But I'm still figuring out how I will save it back into the file and where it'll be inserted from. I know this is the logic needed though. 

-- 12/5 6:54pm -- 

 - Updated the insert function to account for the new split function. 
 rewrote the insert function so that it calls the split function by having left and right nodes. 

 -- 12/5 7:02pm --

  - The split function was now having a new issue where it said it expected 31 items to split. but i realized that I needed to 
  fully account for the space that the keys would take up. 
  - and now the project is fully functional. 