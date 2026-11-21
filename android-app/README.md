# Coptic Slides Android
This is a **native Android WebView application** that loads the existing https://copticslides.netlify.app/ website in its own Android app window. It is not a PWA or a home-screen shortcut. It shares website updates, liturgy, calendar, song slides and readings with the web version.

## Download an APK
Open the GitHub repository's **Actions** tab, select **Build Coptic Slides Android APK**, run the workflow (or open the latest successful run), and download the **CopticSlides-Android-APK** artifact. Unzip it and install `app-debug.apk` on your Android device. Android may ask you to permit installation from that source.

This debug APK is intended for personal testing. A production APK needs a persistent release signing key and a release build. The GitHub workflow intentionally does not store or expose signing secrets.

## Important
- Website content is online and loads in the app, so internet access is required for live updates and Bible Gateway passages.
- The app does not bypass Bible Gateway's iframe or licensing restrictions.
- Native WebView storage is separate from Chrome; website login or browser-only notes may need to be entered again in the app.
- Android app updates that change native code require a new APK; website content updates do not.
