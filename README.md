# Slack Track
Tracks changes to the user base of your Slack instance across a given time period

## Note: WIP
This is a work-in-progress made for my own use. It will have many breaking changes until it gets a 0.1 version, which may never come.
You are free to use and build upon this if you want, but should in no way expect it to be good or consistent.

### Requirements
1. Some UNIX-like (Linux, macOS) with crontab installed (this is default on most distros).  
2. Also have Python 3.6+ installed.


### Getting started
1. Clone the repo  
2. Run `./setup.sh`  
3. Fill out the info it requests from you  
  a. Profit.  
  b. If you don't want it to run automatically and instead wish to develop with this, be sure to select "manually" when
asked how often the script should run. 
4. Let it run for a few days to cache some data. 
5. Edit the `reports.py` file according to the instructions in the docstring. The reports `main` function will be executed 
at the end of every run of slack_track. Use this to dump basic reports into a text file or do extremely complex analysis on
the data -- it's entirely up to you. This file is git ignored.


### Plans for the future
1. More Detailed Reports -- automatically generate reports with colorful graphs and whatever else managers like to look 
at when it comes to analytics, embedded as standalone HTML docs that can be easily shared or uploaded to Confluence or hosted
on your web server.
2. Easy-to-navigate DB tools, probably utilizing a local webserver to interact with your data and find whatever you want. 


### Contributing
Fork it and open a pull request.


### Is there a warranty or anything
Nah


