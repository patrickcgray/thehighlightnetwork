To give you a basic intro though the important files are:

	-main.py this one does all the routing and imports all the other files to actually bring it together

	-models/

		-dbmodels.py this has all the database models in it, they are pretty self explanatory
	
	-pagehandlers/ this is the folder where 90% of the code is. Don't worry about any of the compiled python code, I actually need to take that out of there now.

		-basehandler.py this is the handler that the other files inherit from and I also have the user authentication (using SimpleAuth) done in here.
		
		-otherhandlers.py these all are labeled so that you should be able to make sense of them. The code for some random pages that didn't need their own folder are here.
		
		-profilehandlers.py again pretty self explainatory, the user pages are done in here
		
		-videohandlers.py this is the largest one and all the video uploading, handling and what not is done here.

	-templates/ this folder has all the HTML in it.

There isn't anything too crazy going on, just a good bit of code to check out. I'm using Jinja2 so where you see self.render('HTML_file', variables) those 
are just the variables that I pass to the Jinja2 template which allows me to use some python within the HTML code. The webapp2 framework is what does the 
routing and actually provides the structure to the app is also relatively simple and basically all the classes you see in python are a single type of web 
page in the webapp. 