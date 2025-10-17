A flask web app to visualize participant data for a variety of data collection steps, ranging from fMRI analysis to smartphone sensor tracking.

## This is not an app which is online-- for data privacy, each user must run the site themselves. This is a wrapper so that people with access to the data can view it in an interactive way. 


To run this app, first open up your terminal, and navigate to this folder. 
`cd ~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data-dashboard/data-dashboard`

If you have conda set up, you can create a virtual environment:
`conda create --name pcx-dashboard` 
`conda activate pcx-dashboard` 

Then, in MacOS run:
`pip install -r requirements.txt`

In Windows PowerShell:
`pip install -r ".\requirements.txt"`



Then run this:
`python3 app.py`

You should have an output which says: 
```bash
(base) user@ data-dashboard-v2 % python3 app.py
Dash is running on http://127.0.0.1:8090/

 * Serving Flask app 'app'
 * Debug mode: on
```

Now navigate to any browser, and go to: "http://127.0.0.1:8090/"

You should see the app dashboard there. 

If there are any errors which crash the site, you'll see those errors populate in the terminal, and no URL will be provided.

If there are errors but the site is still running, go to the URL http://127.0.0.1:8090/ and check the "Callbacks" popup to see what the errors are. 