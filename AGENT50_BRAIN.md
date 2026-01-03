# AGENT 50 SUPREME — SYSTEM MEMORY SEAL
**DO NOT DELETE OR MOVE THIS FILE**
**Root Directory:** `C:\Users\ADMIN\Desktop\AGENT50_SUPREME_CORE`
**Last Updated:** 31 December 2025
**Status:** ACTIVE (In Review on Google Play)

---

## 1. PROJECT IDENTITY & VERSION
* **App Name:** Indian Restaurant Hanoi (Agent 50 Customer)
* **Package Name:** `com.hilltopcurry.agent50.customer`
* **Current Version Code:** `4`
* **Current Version Name:** `1.0.0`
* **Distribution:** Android (Google Play Store) & Web
* **Release Track:** Closed Testing (Alpha)

## 2. TECHNOLOGY STACK (IMMUTABLE)
* **Frontend:** React Native (Expo)
    * *Path:* `/frontend/customer`
    * *Build Tool:* EAS CLI (`eas build --platform android`)
* **Backend:** Python (Flask)
    * *Path:* `/backend`
    * *Host:* Vercel (Production) / Localhost (Dev)
    * *Database:* Connected via Environment Variables
* **Version Control:** Git (Single Repository Root)

## 3. SOLVED ISSUES (THE "DO NOT RELEARN" LIST)
* **OS Compatibility:** We are running on **Windows 10/11**.
    * *Rule:* Do NOT attempt to install `fcntl` or Linux-specific packages for local Python development. Use `waitress` or standard Flask run.
* **Build Context:**
    * *Rule:* NEVER run `eas build` from the root or backend. ALWAYS navigate to `frontend/customer` first.
* **Git Fragmentation:**
    * *Rule:* We successfully force-pushed to unify the history. Do not create new repos. Handle "refusing to merge unrelated histories" with `--allow-unrelated-histories` or force push if authorized.
* **Play Store Policy:**
    * *Advertising ID:* We have declared "NO" to Advertising ID usage.
    * *Testers:* We are in "Closed Testing". We need 20 testers for 14 days before Production access.

## 4. DEPLOYMENT PROTOCOL (SOP)
**To Create a New Android Build:**
1.  Open Terminal.
2.  `cd frontend/customer`
3.  `eas build --platform android`
4.  Download `.aab` from the resulting link.
5.  Upload to Google Play Console -> Closed Testing -> Create Release.

**To Update Backend:**
1.  `cd backend`
2.  `git add .`
3.  `git commit -m "update message"`
4.  `git push` (Vercel automatically deploys).

## 5. CONTINUITY PLEDGE (AGENT 50 SUPREME)
I, the AI Agent, acknowledge the following constraints for all future interactions:
1.  **NO NEW FOLDERS:** I will not suggest creating "temp" or "fix" folders. Work happens here.
2.  **NO RESTARTING:** I will not ask "how do I set up the environment?". I assume the environment is set up and working.
3.  **ERROR HANDLING:** If a build fails, I debug the code, not the folder structure.
4.  **MEMORY:** I will reference this file before proposing architectural changes.

---
*End of Memory Record*