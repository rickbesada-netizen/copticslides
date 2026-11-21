package com.copticslides.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Button;

public class MainActivity extends Activity {
    private static final String HOME = "https://copticslides.netlify.app/";
    private WebView web;
    private ProgressBar progress;
    private FrameLayout fullScreenContainer;
    private View customView;
    private WebChromeClient.CustomViewCallback customCallback;
    private WebChromeClient chromeClient;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(18,42,48));
        getWindow().setNavigationBarColor(Color.BLACK);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        FrameLayout.LayoutParams fill = new FrameLayout.LayoutParams(-1,-1);
        root.addView(content, fill);
        fullScreenContainer = new FrameLayout(this);
        root.addView(fullScreenContainer, fill);
        fullScreenContainer.setVisibility(View.GONE);

        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setBackgroundColor(Color.rgb(18,42,48));
        addButton(toolbar, "⌂", () -> web.loadUrl(HOME));
        addButton(toolbar, "‹", () -> { if(web.canGoBack()) web.goBack(); });
        addButton(toolbar, "↻", () -> web.reload());
        TextView title = new TextView(this);
        title.setText("Coptic Slides");
        title.setTextColor(Color.rgb(245,215,153));
        title.setTextSize(17);
        title.setPadding(12,0,0,0);
        toolbar.addView(title, new LinearLayout.LayoutParams(0, 56 * getResources().getDisplayMetrics().densityDpi / 160, 1));
        content.addView(toolbar);

        progress = new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100);
        content.addView(progress,new LinearLayout.LayoutParams(-1,4));
        web = new WebView(this);
        web.setBackgroundColor(Color.BLACK);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setMediaPlaybackRequiresUserGesture(true);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri=request.getUrl();
                if ("https".equalsIgnoreCase(uri.getScheme()) && "copticslides.netlify.app".equalsIgnoreCase(uri.getHost())) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW,uri)); } catch (Exception ignored) {}
                return true;
            }
        });
        chromeClient = new WebChromeClient() {
            @Override public void onProgressChanged(WebView view,int p) { progress.setProgress(p); progress.setVisibility(p==100?View.GONE:View.VISIBLE); }
            @Override public void onShowCustomView(View view, CustomViewCallback callback) {
                if(customView!=null){callback.onCustomViewHidden();return;}
                customView=view;customCallback=callback;
                fullScreenContainer.addView(view,new FrameLayout.LayoutParams(-1,-1));
                fullScreenContainer.setVisibility(View.VISIBLE);
                content.setVisibility(View.GONE);
            }
            @Override public void onHideCustomView() { closeFullscreen(content); }
        };
        web.setWebChromeClient(chromeClient);
        content.addView(web,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);
        if(savedInstanceState!=null) web.restoreState(savedInstanceState);
        else web.loadUrl(HOME);
    }
    private void addButton(LinearLayout bar,String text,Runnable action) {
        Button b=new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setAllCaps(false);
        b.setOnClickListener(v->action.run());
        bar.addView(b,new LinearLayout.LayoutParams(58 * getResources().getDisplayMetrics().densityDpi / 160,-2));
    }
    private void closeFullscreen(LinearLayout content) {
        if(customView==null)return;
        fullScreenContainer.removeView(customView);
        fullScreenContainer.setVisibility(View.GONE);
        content.setVisibility(View.VISIBLE);
        customView=null;
        if(customCallback!=null)customCallback.onCustomViewHidden();
        customCallback=null;
    }
    @Override public void onBackPressed() {
        if(customView!=null){chromeClient.onHideCustomView();return;}
        if(web.canGoBack()){web.goBack();return;}
        super.onBackPressed();
    }
    @Override protected void onSaveInstanceState(Bundle out) { web.saveState(out);super.onSaveInstanceState(out); }
    @Override protected void onDestroy(){web.destroy();super.onDestroy();}
}
