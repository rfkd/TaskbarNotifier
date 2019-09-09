# **Taskbar Notifier**

Taskbar Notifier is running in the system tray and watches for applications on the taskbar. Once an application with a matching title appears or a running application changes its title to one of the setup patterns a Windows toast notification will appear. If configured, the toast notification will be repeated continuously as long as the application title matches. The application was originally written for Microsoft Outlook reminders opening in the background.

### **INSTALLING THE BINARY PACKAGE**
Download the latest [release package](https://github.com/rfkd/TaskbarNotifier/releases) from GitHub, extract the archive to any directory and start *TaskbarNotifier.exe* - it is advisable to add Taskbar Notifier to the Windows autostart. To configure Taskbar Notifier double-click the bell icon in the system tray and adjust watch expressions and settings.

### **BUILDING FROM SOURCES**
To build Taskbar Notifier from sources [Python 3](https://www.python.org/downloads) needs to be installed first. Then perform the following steps:

1. Clone the Taskbar Notifier repository. The **master** branch contains stable versions while the **develop** branch contains a current development snapshot with the latest features and fixes.

   To get the latest stable version from the **master** branch run:
   ```
   $ git clone -b master https://github.com/rfkd/TaskbarNotifier.git
   ```
   
   To get the latest development version from the **develop** branch run:
   ```
   $ git clone https://github.com/rfkd/TaskbarNotifier.git
   ```
   
2. ***Optional but strongly recommended:*** Create and start a virtual Python environment (e.g. [virtualenv](https://virtualenv.pypa.io) and [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io)) in the previously cloned repository.

3. Install the required Python packages:
   ```
   $ pip install -r requirements.txt
   ```
   
4. Call the build script:
   ```
   $ python build.py
   ```
   
Once built Taskbar Notifier will be copied to the `dist` subdirectory.

