# <> Denotes a variable

############
## BASICS ##
############

# Clone an existing repository
git clone <link>

# Basic Information
git status

# Add new files to track
git add <filename>

# You can use wildcards as follows
git add src/*

# Report ignored files in .gitignore

# Commit your changes when the program is at a stable point
git commit

# Optionally with the -m flag to write the message at the same time
git commit -m "<Message>"

# Optionally with -a flag to add all unstaged changes
git commit -a -m "<Message>"

# IMPORTANT: To remove a file from the directory you cannot just rm it
git rm <filename>

# IMPORTANT: If by mistake you add a file you dont want to 
# Use this command to remove it from git but not from your directory
git rm --cached <filename>

# Wildcards in git rm look like this
git rm \*<file_ending>

# It is a good thing to rename files like this
git mv <old_filename> <new_filename>

# View the commit history
git log

# For further reading on git log visit the official documentation

########################
## UNDO YOUR MISTAKES ##
########################

# Overwrite a mistaken commit
# Either because you messed up the message or didnt add some files
git commit --amend

# Unstage a file
git reser HEAD <filename>

# If you destroy a file and cannot remember its initial state
# The following command reverts a file before your changes
# WARNING: Please dont play with this command ( It just deletes your copy ) 
git checkout -- <filename>

##################
## REMOTE REPOS ##
##################

# TODO: Check this link and finish the guide
https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes
