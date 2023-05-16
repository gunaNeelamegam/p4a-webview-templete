# p4a-webview-templete
p4a-webview-template

### STEPS TO FOLLOW:
  
  - prerequites:
  -  linux:
  -   `sudo apt install openjdk-11-jdk`
  -   `pip install python-for-android`
  -   `pip install buildozer`
  
 1, clone the branch using git clone reposistory-url
 
 ## debug the android app
command: 

  *`buildozer android debug`*
 
 ## deploy into real device or emulator 
 
 command:
 
  *`builozer android debug deploy`*
  
  
 ### NOTE:
 - If you need to change the name of the project as of now named as (testapp)
 - All the configuration are present inside the  buildozer.spec file change as you need.
 - Project is fully based on flask based android app
 - All the ui based html content are placed inside the templates folder inside the project directory.
 - buildozer takes the reponsiable to load the main.py file inside the root directory.
 
