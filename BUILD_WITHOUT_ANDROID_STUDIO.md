# Build Mwaeche HMS APK without installing Android Studio

This starter can be built on GitHub's hosted build machines. You do not need to install Android Studio on your own computer, but you do need a GitHub account and must upload this project to a repository.

## Steps
1. Sign in to GitHub and create a **private** repository, e.g. `mwaeche-hms-android`.
2. Upload the contents of this folder to the repository. Keep `.github/workflows/build-android.yml` in that exact path and keep the `android` folder at repository root.
3. Open the repository's **Actions** tab and select **Build Mwaeche HMS Android APK**.
4. Click **Run workflow** if it has not run automatically after upload.
5. When the run succeeds, open the completed workflow run and download the artifact named `mwaeche-hms-android-debug-apk`.
6. Extract the artifact ZIP. It contains `app-debug.apk`; transfer it to your Android device and install it for development testing.

## Important limitations
- This builds the current starter app only. It is not the complete hospital-management app.
- A debug APK is for testing, not production distribution. A production release needs a signing key, security review, and device testing.
- The current app only has a server connection test screen. The full modules and production server integration are not complete.
- Do not upload real patient data, database backups, passwords, API secrets, or private signing keys to the repository.
- The server must be deployed securely behind HTTPS before connecting real patient records. Do not expose the desktop app's unrestricted SQL endpoint.
