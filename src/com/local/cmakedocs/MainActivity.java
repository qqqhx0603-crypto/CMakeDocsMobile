package com.local.cmakedocs;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.SeekBar;
import android.widget.TextView;
import android.text.Editable;
import android.text.TextWatcher;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

public class MainActivity extends Activity {
    private static final String PREFS = "cmake_docs_state";
    private static final String ASSET_BASE = "file:///android_asset/docs/";
    private static final int MAX_HISTORY = 30;
    private static final int CONTENT_VERSION = 6;

    private WebView webView;
    private WebView standbyWebView;
    private WebView loadingWebView;
    private FrameLayout webContainer;
    private Button backButton;
    private Button forwardButton;
    private Button langButton;
    private Button starButton;
    private TextView titleView;
    private SeekBar progressBar;

    private final ArrayList<Entry> history = new ArrayList<>();
    private int historyIndex = -1;
    private boolean loadingFromHistory = false;
    private boolean skipNextPageStartedCapture = false;
    private boolean userDraggingProgress = false;
    private boolean pageLoading = false;
    private boolean hasDisplayedPage = false;
    private boolean loadingPageStarted = false;
    private boolean loadingPageFinished = false;
    private int loadGeneration = 0;
    private String expectedLoadLang = "zh";
    private String expectedLoadPath = "index.html";
    private int pendingScrollY = 0;
    private float pendingScrollRatio = -1f;

    private String currentLang = "zh";
    private String currentPath = "index.html";
    private String displayedLang = "zh";
    private String displayedPath = "index.html";
    private int textZoom = 100;

    private final Map<String, ArrayList<PageInfo>> pages = new HashMap<>();
    private final Map<String, HashSet<String>> pagePathSets = new HashMap<>();
    private final LinkedHashSet<String> favorites = new LinkedHashSet<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        loadIndex();
        buildUi();
        clearCacheIfNeeded();
        restoreState();

        if (historyIndex >= 0 && historyIndex < history.size()) {
            Entry entry = history.get(historyIndex);
            loadingFromHistory = true;
            loadEntry(entry);
        } else {
            loadPage("zh", "index.html");
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        captureCurrentScroll();
        saveState();
    }

    @Override
    protected void onStop() {
        super.onStop();
        captureCurrentScroll();
        saveState();
    }

    private void buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.WHITE);
        configureSystemBars(root);

        titleView = new TextView(this);
        titleView.setSingleLine(true);
        titleView.setTextColor(Color.rgb(30, 30, 30));
        titleView.setTextSize(15);
        titleView.setPadding(dp(10), dp(8), dp(10), dp(4));
        root.addView(titleView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setOrientation(LinearLayout.VERTICAL);
        toolbar.setPadding(dp(6), dp(2), dp(6), dp(4));
        LinearLayout toolbarRow1 = makeToolbarRow();
        LinearLayout toolbarRow2 = makeToolbarRow();

        backButton = makeButton("◀");
        forwardButton = makeButton("▶");
        Button homeButton = makeButton("Home");
        langButton = makeButton("EN");
        Button searchButton = makeButton("搜索");
        Button listButton = makeButton("目录");
        Button favListButton = makeButton("收藏");
        starButton = makeButton("☆");
        Button topButton = makeButton("顶部");
        Button bottomButton = makeButton("底部");
        Button zoomOutButton = makeButton("A-");
        Button zoomInButton = makeButton("A+");

        toolbarRow1.addView(backButton);
        toolbarRow1.addView(forwardButton);
        toolbarRow1.addView(homeButton);
        toolbarRow1.addView(langButton);
        toolbarRow1.addView(searchButton);
        toolbarRow1.addView(listButton);
        toolbarRow2.addView(favListButton);
        toolbarRow2.addView(starButton);
        toolbarRow2.addView(topButton);
        toolbarRow2.addView(bottomButton);
        toolbarRow2.addView(zoomOutButton);
        toolbarRow2.addView(zoomInButton);
        toolbar.addView(toolbarRow1);
        toolbar.addView(toolbarRow2);
        root.addView(toolbar, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        progressBar = new SeekBar(this);
        progressBar.setMax(1000);
        progressBar.setPadding(dp(10), 0, dp(10), 0);
        root.addView(progressBar, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(30)));

        webContainer = new FrameLayout(this);
        webView = createDocsWebView();
        standbyWebView = createDocsWebView();
        standbyWebView.setVisibility(View.INVISIBLE);
        webContainer.addView(standbyWebView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        webContainer.addView(webView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        root.addView(webContainer, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

        setContentView(root);

        backButton.setOnClickListener(v -> goBackInHistory());
        forwardButton.setOnClickListener(v -> goForwardInHistory());
        homeButton.setOnClickListener(v -> loadPage(currentLang, "index.html"));
        langButton.setOnClickListener(v -> switchLanguage());
        searchButton.setOnClickListener(v -> showSearchDialog());
        listButton.setOnClickListener(v -> showPagePicker());
        favListButton.setOnClickListener(v -> showFavorites());
        starButton.setOnClickListener(v -> toggleFavorite());
        topButton.setOnClickListener(v -> scrollToTop());
        bottomButton.setOnClickListener(v -> scrollToBottom());
        zoomOutButton.setOnClickListener(v -> {
            textZoom = Math.max(60, textZoom - 10);
            applyTextZoom();
        });
        zoomInButton.setOnClickListener(v -> {
            textZoom = Math.min(220, textZoom + 10);
            applyTextZoom();
        });
        progressBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                if (fromUser) {
                    scrollToProgress(progress);
                }
            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {
                userDraggingProgress = true;
            }

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {
                userDraggingProgress = false;
                scrollToProgress(seekBar.getProgress());
                captureCurrentScroll();
                saveState();
            }
        });
    }

    private void applyTextZoom() {
        webView.getSettings().setTextZoom(textZoom);
        standbyWebView.getSettings().setTextZoom(textZoom);
        saveState();
    }

    private WebView createDocsWebView() {
        WebView view = new WebView(this);
        WebSettings settings = view.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setSupportZoom(true);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(false);
        settings.setLayoutAlgorithm(WebSettings.LayoutAlgorithm.TEXT_AUTOSIZING);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setTextZoom(textZoom);
        view.setWebViewClient(new DocsWebViewClient());
        view.setOnScrollChangeListener((v, scrollX, scrollY, oldScrollX, oldScrollY) -> {
            if (v == webView && !userDraggingProgress) {
                updateScrollProgress();
            }
        });
        return view;
    }

    private void configureSystemBars(View root) {
        getWindow().setStatusBarColor(Color.WHITE);
        getWindow().setNavigationBarColor(Color.WHITE);
        if (Build.VERSION.SDK_INT >= 23) {
            getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
        }
        if (Build.VERSION.SDK_INT >= 30) {
            getWindow().setDecorFitsSystemWindows(false);
            root.setOnApplyWindowInsetsListener((view, insets) -> {
                int top = insets.getSystemWindowInsetTop();
                int bottom = insets.getSystemWindowInsetBottom();
                view.setPadding(0, top, 0, bottom);
                return insets;
            });
            root.requestApplyInsets();
        } else {
            root.setFitsSystemWindows(true);
        }
    }

    private LinearLayout makeToolbarRow() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setPadding(0, dp(2), 0, dp(2));
        row.setBaselineAligned(false);
        return row;
    }

    private Button makeButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setAllCaps(false);
        button.setTextSize(13);
        button.setMinWidth(0);
        button.setMinimumWidth(0);
        button.setMinHeight(dp(36));
        button.setPadding(dp(2), 0, dp(2), 0);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                0, dp(38), 1);
        params.setMargins(dp(2), 0, dp(2), 0);
        button.setLayoutParams(params);
        return button;
    }

    private void loadIndex() {
        pages.put("zh", new ArrayList<>());
        pages.put("en", new ArrayList<>());
        pagePathSets.put("zh", new HashSet<>());
        pagePathSets.put("en", new HashSet<>());
        try {
            JSONObject root = new JSONObject(readAssetText("docs_index.json"));
            loadLangIndex(root, "zh");
            loadLangIndex(root, "en");
        } catch (Exception ignored) {
            addFallbackIndex("zh");
            addFallbackIndex("en");
        }
    }

    private void loadLangIndex(JSONObject root, String lang) throws Exception {
        JSONArray array = root.getJSONArray(lang);
        ArrayList<PageInfo> list = pages.get(lang);
        HashSet<String> set = pagePathSets.get(lang);
        for (int i = 0; i < array.length(); i++) {
            JSONObject item = array.getJSONObject(i);
            String path = item.getString("path");
            String title = item.optString("title", path);
            String keywords = item.optString("keywords", "");
            String summary = item.optString("summary", "");
            list.add(new PageInfo(lang, path, title, keywords, summary));
            set.add(stripFragment(path));
        }
    }

    private void addFallbackIndex(String lang) {
        ArrayList<PageInfo> list = pages.get(lang);
        HashSet<String> set = pagePathSets.get(lang);
        list.add(new PageInfo(lang, "index.html", "CMake", "CMake index", ""));
        list.add(new PageInfo(lang, "search.html", "Search", "search", ""));
        set.add("index.html");
        set.add("search.html");
    }

    private String readAssetText(String name) throws Exception {
        InputStream input = getAssets().open(name);
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int n;
        while ((n = input.read(buffer)) >= 0) {
            output.write(buffer, 0, n);
        }
        input.close();
        return output.toString("UTF-8");
    }

    private void loadPage(String lang, String path) {
        captureCurrentScroll();
        currentLang = lang;
        currentPath = normalizePath(path);
        loadingFromHistory = false;
        pendingScrollY = 0;
        pendingScrollRatio = -1f;
        startLoadingCurrentPage();
    }

    private void startLoadingCurrentPage() {
        WebView target = hasDisplayedPage ? standbyWebView : webView;
        loadingWebView = target;
        pageLoading = true;
        loadGeneration++;
        expectedLoadLang = currentLang;
        expectedLoadPath = normalizePath(currentPath);
        loadingPageStarted = false;
        loadingPageFinished = false;
        skipNextPageStartedCapture = true;
        target.stopLoading();
        target.getSettings().setTextZoom(textZoom);
        target.scrollTo(0, 0);
        if (target != webView) {
            target.setVisibility(View.INVISIBLE);
        }
        updateScrollProgress();
        target.loadUrl(toAssetUrl(currentLang, currentPath));
    }

    private void loadEntry(Entry entry) {
        currentLang = entry.lang;
        currentPath = normalizePath(entry.path);
        pendingScrollY = entry.scrollY;
        pendingScrollRatio = -1f;
        startLoadingCurrentPage();
    }

    private String toAssetUrl(String lang, String path) {
        String clean = normalizePath(path);
        String fragment = "";
        int hash = clean.indexOf('#');
        if (hash >= 0) {
            fragment = clean.substring(hash);
            clean = clean.substring(0, hash);
        }
        return ASSET_BASE + lang + "/" + Uri.encode(clean, "/.@_-") + fragment;
    }

    private String normalizePath(String path) {
        if (path == null || path.trim().length() == 0) {
            return "index.html";
        }
        String result = path.replace('\\', '/');
        while (result.startsWith("/")) {
            result = result.substring(1);
        }
        if (result.length() == 0) {
            return "index.html";
        }
        return result;
    }

    private void pushHistory(String lang, String path) {
        path = normalizePath(path);
        if (historyIndex >= 0 && historyIndex < history.size()) {
            Entry current = history.get(historyIndex);
            if (current.lang.equals(lang) && current.path.equals(path)) {
                updateControls();
                return;
            }
        }
        while (history.size() > historyIndex + 1) {
            history.remove(history.size() - 1);
        }
        history.add(new Entry(lang, path, pendingScrollY));
        while (history.size() > MAX_HISTORY) {
            history.remove(0);
        }
        historyIndex = history.size() - 1;
        saveState(false);
    }

    private void goBackInHistory() {
        if (historyIndex <= 0) {
            return;
        }
        captureCurrentScroll();
        historyIndex--;
        loadingFromHistory = true;
        Entry entry = history.get(historyIndex);
        currentLang = entry.lang;
        currentPath = normalizePath(entry.path);
        pendingScrollY = entry.scrollY;
        pendingScrollRatio = -1f;
        startLoadingCurrentPage();
        saveState(false);
    }

    private void goForwardInHistory() {
        if (historyIndex >= history.size() - 1) {
            return;
        }
        captureCurrentScroll();
        historyIndex++;
        loadingFromHistory = true;
        Entry entry = history.get(historyIndex);
        currentLang = entry.lang;
        currentPath = normalizePath(entry.path);
        pendingScrollY = entry.scrollY;
        pendingScrollRatio = -1f;
        startLoadingCurrentPage();
        saveState(false);
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && historyIndex > 0) {
            goBackInHistory();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    private void switchLanguage() {
        String other = currentLang.equals("zh") ? "en" : "zh";
        if (!hasPage(other, currentPath)) {
            return;
        }
        captureCurrentScroll();
        int range = getScrollableRange(webView);
        pendingScrollRatio = range <= 0
                ? 0f
                : Math.max(0f, Math.min(1f, webView.getScrollY() / (float) range));
        currentLang = other;
        currentPath = normalizePath(currentPath);
        loadingFromHistory = false;
        pendingScrollY = 0;
        startLoadingCurrentPage();
    }

    private boolean hasPage(String lang, String path) {
        HashSet<String> set = pagePathSets.get(lang);
        return set != null && set.contains(stripFragment(path));
    }

    private String stripFragment(String path) {
        String clean = normalizePath(path);
        int hash = clean.indexOf('#');
        if (hash >= 0) {
            clean = clean.substring(0, hash);
        }
        return clean;
    }

    private void toggleFavorite() {
        String key = currentLang + "|" + currentPath;
        if (favorites.contains(key)) {
            favorites.remove(key);
        } else {
            favorites.add(key);
        }
        saveState();
        updateControls();
    }

    private void showFavorites() {
        ArrayList<String> items = new ArrayList<>();
        ArrayList<Entry> entries = new ArrayList<>();
        for (String key : favorites) {
            String[] parts = key.split("\\|", 2);
            if (parts.length == 2) {
                Entry entry = new Entry(parts[0], parts[1]);
                entries.add(entry);
                items.add(languageLabel(parts[0]) + "  " + titleFor(parts[0], parts[1]));
            }
        }
        if (items.isEmpty()) {
            items.add("暂无收藏");
        }
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("收藏");
        builder.setItems(items.toArray(new String[0]), (dialog, which) -> {
            if (which < entries.size()) {
                Entry entry = entries.get(which);
                loadPage(entry.lang, entry.path);
            }
        });
        builder.setNegativeButton("关闭", null);
        builder.show();
    }

    private void showSearchDialog() {
        final String lang = currentLang;
        ArrayList<PageInfo> source = pages.get(lang);
        if (source == null) {
            source = new ArrayList<>();
        }

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int padding = dp(14);
        layout.setPadding(padding, padding, padding, padding);

        EditText input = new EditText(this);
        input.setHint("输入命令、标题或路径");
        input.setSingleLine(true);
        layout.addView(input, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        ListView listView = new ListView(this);
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this, android.R.layout.simple_list_item_1);
        listView.setAdapter(adapter);
        layout.addView(listView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(430)));

        final ArrayList<PageInfo> shown = new ArrayList<>();
        ArrayList<PageInfo> finalSource = source;
        Runnable[] refill = new Runnable[1];
        refill[0] = () -> {
            String q = input.getText().toString().toLowerCase(Locale.ROOT).trim();
            adapter.clear();
            shown.clear();
            if (q.length() == 0) {
                adapter.add("请输入关键词，例如 cmake、install、generator");
            } else {
                for (PageInfo info : finalSource) {
                    String hay = info.searchBlob();
                    if (hay.contains(q)) {
                        shown.add(info);
                        adapter.add(info.listLabel());
                        if (shown.size() >= 260) {
                            break;
                        }
                    }
                }
                if (shown.isEmpty()) {
                    adapter.add("未找到匹配页面");
                }
            }
            adapter.notifyDataSetChanged();
        };

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("搜索 - " + languageLabel(lang))
                .setView(layout)
                .setNegativeButton("关闭", null)
                .create();

        listView.setOnItemClickListener((AdapterView<?> parent, View view, int position, long id) -> {
            if (position < shown.size()) {
                PageInfo info = shown.get(position);
                dialog.dismiss();
                loadPage(info.lang, info.path);
            }
        });

        input.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { refill[0].run(); }
            @Override public void afterTextChanged(Editable s) {}
        });

        dialog.setOnShowListener(d -> {
            refill[0].run();
            input.requestFocus();
        });
        dialog.show();
    }

    private void showPagePicker() {
        final String lang = currentLang;
        ArrayList<PageInfo> source = pages.get(lang);
        if (source == null) {
            source = new ArrayList<>();
        }

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int padding = dp(14);
        layout.setPadding(padding, padding, padding, padding);

        EditText input = new EditText(this);
        input.setHint("输入标题、命令或路径");
        input.setSingleLine(true);
        layout.addView(input, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        ListView listView = new ListView(this);
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this, android.R.layout.simple_list_item_1);
        listView.setAdapter(adapter);
        layout.addView(listView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(430)));

        final ArrayList<String> shownKinds = new ArrayList<>();
        final ArrayList<String> shownTargets = new ArrayList<>();
        final ArrayList<PageInfo> shownPages = new ArrayList<>();
        final String[] folder = new String[] { folderOf(currentPath) };
        final AlertDialog[] dialogRef = new AlertDialog[1];
        Runnable[] refill = new Runnable[1];
        ArrayList<PageInfo> finalSource = source;
        refill[0] = () -> {
            String q = input.getText().toString().toLowerCase(Locale.ROOT).trim();
            adapter.clear();
            shownKinds.clear();
            shownTargets.clear();
            shownPages.clear();

            if (dialogRef[0] != null) {
                dialogRef[0].setTitle("目录 - " + languageLabel(lang) + " / " + folderLabel(folder[0]));
            }

            if (q.length() > 0) {
                for (PageInfo info : finalSource) {
                    String hay = info.searchBlob();
                    if (hay.contains(q)) {
                        addPickerRow(adapter, shownKinds, shownTargets, shownPages,
                                "page", info.path, info, "🔎 " + info.listLabel());
                        if (shownPages.size() >= 260) {
                            break;
                        }
                    }
                }
            } else {
                if (folder[0].length() > 0) {
                    addPickerRow(adapter, shownKinds, shownTargets, shownPages,
                            "up", parentFolder(folder[0]), null, "↑ 上一级");
                }

                TreeSet<String> childFolders = new TreeSet<>();
                ArrayList<PageInfo> childPages = new ArrayList<>();
                for (PageInfo info : finalSource) {
                    String clean = stripFragment(info.path);
                    if (!clean.startsWith(folder[0])) {
                        continue;
                    }
                    String rest = clean.substring(folder[0].length());
                    if (rest.length() == 0) {
                        continue;
                    }
                    int slash = rest.indexOf('/');
                    if (slash >= 0) {
                        childFolders.add(folder[0] + rest.substring(0, slash + 1));
                    } else {
                        childPages.add(info);
                    }
                }

                for (String child : childFolders) {
                    addPickerRow(adapter, shownKinds, shownTargets, shownPages,
                            "folder", child, null, "📁 " + lastFolderName(child));
                }
                for (PageInfo info : childPages) {
                    addPickerRow(adapter, shownKinds, shownTargets, shownPages,
                            "page", info.path, info, "📄 " + info.listLabel());
                }
            }

            if (shownKinds.isEmpty()) {
                adapter.add("未找到匹配页面");
            }
            adapter.notifyDataSetChanged();
        };

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("目录 - " + languageLabel(lang) + " / " + folderLabel(folder[0]))
                .setView(layout)
                .setNegativeButton("关闭", null)
                .create();
        dialogRef[0] = dialog;

        listView.setOnItemClickListener((AdapterView<?> parent, View view, int position, long id) -> {
            if (position >= shownKinds.size()) {
                return;
            }
            String kind = shownKinds.get(position);
            String target = shownTargets.get(position);
            if ("folder".equals(kind) || "up".equals(kind)) {
                folder[0] = target;
                input.setText("");
                refill[0].run();
                return;
            }
            if ("page".equals(kind)) {
                PageInfo info = shownPages.get(position);
                dialog.dismiss();
                loadPage(info.lang, info.path);
            }
        });

        input.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { refill[0].run(); }
            @Override public void afterTextChanged(Editable s) {}
        });

        dialog.setOnShowListener(d -> refill[0].run());
        dialog.show();
    }

    private void addPickerRow(ArrayAdapter<String> adapter, ArrayList<String> kinds,
                              ArrayList<String> targets, ArrayList<PageInfo> pages,
                              String kind, String target, PageInfo page, String label) {
        kinds.add(kind);
        targets.add(target);
        pages.add(page);
        adapter.add(label);
    }

    private String folderOf(String path) {
        String clean = stripFragment(path);
        int slash = clean.lastIndexOf('/');
        if (slash < 0) {
            return "";
        }
        return clean.substring(0, slash + 1);
    }

    private String parentFolder(String folder) {
        String clean = folder;
        while (clean.endsWith("/") && clean.length() > 0) {
            clean = clean.substring(0, clean.length() - 1);
        }
        int slash = clean.lastIndexOf('/');
        if (slash < 0) {
            return "";
        }
        return clean.substring(0, slash + 1);
    }

    private String folderLabel(String folder) {
        return folder.length() == 0 ? "根目录" : folder;
    }

    private String lastFolderName(String folder) {
        String clean = folder;
        while (clean.endsWith("/") && clean.length() > 0) {
            clean = clean.substring(0, clean.length() - 1);
        }
        int slash = clean.lastIndexOf('/');
        return slash >= 0 ? clean.substring(slash + 1) + "/" : clean + "/";
    }

    private String titleFor(String lang, String path) {
        String clean = stripFragment(path);
        ArrayList<PageInfo> list = pages.get(lang);
        if (list != null) {
            for (PageInfo info : list) {
                if (info.path.equals(clean)) {
                    return info.title;
                }
            }
        }
        return clean;
    }

    private String languageLabel(String lang) {
        return "zh".equals(lang) ? "中文" : "English";
    }

    private void updateControls() {
        backButton.setEnabled(historyIndex > 0);
        forwardButton.setEnabled(historyIndex >= 0 && historyIndex < history.size() - 1);
        backButton.setAlpha(backButton.isEnabled() ? 1.0f : 0.35f);
        forwardButton.setAlpha(forwardButton.isEnabled() ? 1.0f : 0.35f);

        String shownLang = displayedLang;
        String shownPath = displayedPath;
        String other = shownLang.equals("zh") ? "en" : "zh";
        langButton.setText(shownLang.equals("zh") ? "EN" : "中文");
        langButton.setEnabled(!pageLoading && hasPage(other, shownPath));
        langButton.setAlpha(langButton.isEnabled() ? 1.0f : 0.35f);

        starButton.setText(favorites.contains(shownLang + "|" + shownPath) ? "★" : "☆");
        titleView.setText(languageLabel(shownLang) + " · " + titleFor(shownLang, shownPath));
    }

    private void saveState() {
        saveState(true);
    }

    private void saveState(boolean captureScroll) {
        if (captureScroll) {
            captureCurrentScroll();
        }
        try {
            JSONArray hist = new JSONArray();
            for (Entry entry : history) {
                JSONObject item = new JSONObject();
                item.put("lang", entry.lang);
                item.put("path", entry.path);
                item.put("scrollY", entry.scrollY);
                hist.put(item);
            }
            JSONArray fav = new JSONArray();
            for (String key : favorites) {
                fav.put(key);
            }
            SharedPreferences.Editor editor = getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit();
            editor.putString("history", hist.toString());
            editor.putInt("historyIndex", historyIndex);
            editor.putString("favorites", fav.toString());
            editor.putString("currentLang", currentLang);
            editor.putString("currentPath", currentPath);
            editor.putInt("textZoom", textZoom);
            editor.apply();
        } catch (Exception ignored) {}
    }

    private void restoreState() {
        SharedPreferences prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        textZoom = prefs.getInt("textZoom", 100);
        if (webView != null) {
            webView.getSettings().setTextZoom(textZoom);
        }
        try {
            JSONArray hist = new JSONArray(prefs.getString("history", "[]"));
            for (int i = 0; i < hist.length(); i++) {
                JSONObject item = hist.getJSONObject(i);
                String lang = item.optString("lang", "zh");
                String path = item.optString("path", "index.html");
                if (hasPage(lang, path)) {
                    history.add(new Entry(lang, path, item.optInt("scrollY", 0)));
                }
            }
            historyIndex = prefs.getInt("historyIndex", history.size() - 1);
            if (historyIndex < 0 || historyIndex >= history.size()) {
                historyIndex = history.size() - 1;
            }
        } catch (Exception ignored) {
            history.clear();
            historyIndex = -1;
        }

        try {
            JSONArray fav = new JSONArray(prefs.getString("favorites", "[]"));
            for (int i = 0; i < fav.length(); i++) {
                favorites.add(fav.getString(i));
            }
        } catch (Exception ignored) {}
    }

    private void captureCurrentScroll() {
        if (pageLoading || webView == null || historyIndex < 0 || historyIndex >= history.size()) {
            return;
        }
        Entry entry = history.get(historyIndex);
        if (entry.lang.equals(currentLang) && entry.path.equals(currentPath)) {
            entry.scrollY = webView.getScrollY();
        }
    }

    private void restoreScrollAfterLoad(WebView target) {
        final int targetY = Math.max(0, pendingScrollY);
        final float targetRatio = pendingScrollRatio;
        final int generation = loadGeneration;
        pendingScrollRatio = -1f;
        waitForStableLayoutAndRestore(target, targetY, targetRatio, generation, 0, -1);
    }

    private void waitForStableLayoutAndRestore(WebView target, int targetY, float targetRatio,
                                               int generation, int attempt, int previousRange) {
        target.postDelayed(() -> {
            if (generation != loadGeneration || target != loadingWebView) {
                return;
            }
            int range = getScrollableRange(target);
            boolean needsScrollablePage = targetRatio > 0f || targetY > 0;
            boolean rangeStable = range > 0 && previousRange >= 0 && Math.abs(range - previousRange) <= 2;
            if (needsScrollablePage && attempt < 12 && !rangeStable) {
                waitForStableLayoutAndRestore(target, targetY, targetRatio, generation,
                        attempt + 1, range);
                return;
            }
            if (targetRatio >= 0f) {
                target.scrollTo(0, Math.round(range * Math.max(0f, Math.min(1f, targetRatio))));
            } else if (targetY > 0) {
                target.scrollTo(0, Math.min(targetY, range));
            } else if (!currentPath.contains("#")) {
                target.scrollTo(0, 0);
            }
            makeLoadedWebViewVisible(target);
            updateScrollProgress();
            pageLoading = false;
            captureCurrentScroll();
            saveState(false);
            updateControls();
        }, 100);
    }

    private int getScrollableRange() {
        if (webView == null) {
            return 0;
        }
        int contentHeight = Math.round(webView.getContentHeight() * webView.getScale());
        return Math.max(0, contentHeight - webView.getHeight());
    }

    private int getScrollableRange(WebView view) {
        if (view == null) {
            return 0;
        }
        int contentHeight = Math.round(view.getContentHeight() * view.getScale());
        return Math.max(0, contentHeight - view.getHeight());
    }

    private void makeLoadedWebViewVisible(WebView target) {
        if (target == webView) {
            target.setVisibility(View.VISIBLE);
            hasDisplayedPage = true;
            displayedLang = currentLang;
            displayedPath = currentPath;
            return;
        }
        WebView old = webView;
        webView = target;
        standbyWebView = old;
        webView.setVisibility(View.VISIBLE);
        webView.bringToFront();
        standbyWebView.setVisibility(View.INVISIBLE);
        hasDisplayedPage = true;
        displayedLang = currentLang;
        displayedPath = currentPath;
    }

    private void updateScrollProgress() {
        if (progressBar == null || userDraggingProgress) {
            return;
        }
        int range = getScrollableRange();
        int progress = range <= 0 ? 0 : Math.round((webView.getScrollY() * 1000f) / range);
        progressBar.setProgress(Math.max(0, Math.min(1000, progress)));
    }

    private void scrollToProgress(int progress) {
        int range = getScrollableRange();
        int targetY = Math.round(range * (Math.max(0, Math.min(1000, progress)) / 1000f));
        webView.scrollTo(0, targetY);
    }

    private void scrollToTop() {
        webView.scrollTo(0, 0);
        updateScrollProgress();
        webView.postDelayed(() -> {
            captureCurrentScroll();
            saveState();
        }, 100);
    }

    private void scrollToBottom() {
        webView.scrollTo(0, getScrollableRange());
        updateScrollProgress();
        webView.postDelayed(() -> {
            captureCurrentScroll();
            saveState();
        }, 100);
    }

    private void clearCacheIfNeeded() {
        SharedPreferences prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        if (prefs.getInt("contentVersion", 0) != CONTENT_VERSION) {
            webView.clearCache(true);
            standbyWebView.clearCache(true);
            prefs.edit().putInt("contentVersion", CONTENT_VERSION).apply();
        }
    }

    private int dp(int value) {
        float density = getResources().getDisplayMetrics().density;
        return Math.round(value * density);
    }

    private class DocsWebViewClient extends WebViewClient {
        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            return handleUrl(request.getUrl().toString());
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, String url) {
            return handleUrl(url);
        }

        private boolean handleUrl(String url) {
            if (url == null) {
                return false;
            }
            if (url.startsWith(ASSET_BASE)) {
                Entry local = parseAssetUrl(url);
                if (local != null && !hasPage(local.lang, local.path)) {
                    loadPage(local.lang, "index.html");
                    return true;
                }
                return false;
            }
            if (url.startsWith("file:///android_asset/docs/")) {
                Entry local = parseAssetUrl(url);
                if (local != null && !hasPage(local.lang, local.path)) {
                    loadPage(local.lang, "index.html");
                    return true;
                }
                return false;
            }
            Entry local = mapExternalCMakeUrl(url);
            if (local != null) {
                loadPage(local.lang, local.path);
                return true;
            }
            if (url.startsWith("http://") || url.startsWith("https://")) {
                return true;
            }
            return false;
        }

        @Override
        public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
            super.onPageStarted(view, url, favicon);
            if (view != loadingWebView) {
                return;
            }
            Entry parsed = parseAssetUrl(url);
            if (!isExpectedLoad(parsed) || loadingPageStarted) {
                return;
            }
            loadingPageStarted = true;
            if (skipNextPageStartedCapture) {
                skipNextPageStartedCapture = false;
            } else if (!loadingFromHistory) {
                captureCurrentScroll();
                pendingScrollY = 0;
                pendingScrollRatio = -1f;
            }
            pageLoading = true;
        }

        @Override
        public void onPageFinished(WebView view, String url) {
            super.onPageFinished(view, url);
            if (view != loadingWebView) {
                return;
            }
            Entry parsed = parseAssetUrl(url);
            if (!loadingPageStarted || !isExpectedLoad(parsed) || loadingPageFinished) {
                return;
            }
            loadingPageFinished = true;
            currentLang = parsed.lang;
            currentPath = parsed.path;
            if (loadingFromHistory) {
                loadingFromHistory = false;
                restoreScrollAfterLoad(view);
                saveState(false);
            } else {
                pushHistory(currentLang, currentPath);
                restoreScrollAfterLoad(view);
            }
        }

        private boolean isExpectedLoad(Entry entry) {
            return entry != null
                    && expectedLoadLang.equals(entry.lang)
                    && expectedLoadPath.equals(normalizePath(entry.path));
        }
    }

    private Entry mapExternalCMakeUrl(String url) {
        try {
            Uri uri = Uri.parse(url);
            String host = uri.getHost();
            if (host == null) {
                return null;
            }
            String lowerHost = host.toLowerCase(Locale.ROOT);
            boolean cmakeHost = lowerHost.equals("cmake.org") || lowerHost.endsWith(".cmake.org")
                    || lowerHost.equals("cmake.com.cn") || lowerHost.endsWith(".cmake.com.cn");
            if (!cmakeHost) {
                return null;
            }

            String path = uri.getPath();
            if (path == null || "/".equals(path) || path.length() == 0) {
                return new Entry(currentLang, "index.html");
            }

            String[] prefixes = new String[] {
                    "/cmake/help/latest/",
                    "/cmake/help/v4.3.4/",
                    "/cmake/help/v4.3/",
                    "/help/latest/",
                    "/help/v4.3.4/",
                    "/help/v4.3/"
            };
            String rel = null;
            for (String prefix : prefixes) {
                if (path.startsWith(prefix)) {
                    rel = path.substring(prefix.length());
                    break;
                }
            }
            if (rel == null) {
                return new Entry(currentLang, "index.html");
            }
            if (rel.length() == 0 || rel.endsWith("/")) {
                rel = rel + "index.html";
            }
            String fragment = uri.getFragment();
            if (fragment != null && fragment.length() > 0) {
                rel = rel + "#" + fragment;
            }
            if (hasPage(currentLang, rel)) {
                return new Entry(currentLang, rel);
            }
            String other = currentLang.equals("zh") ? "en" : "zh";
            if (hasPage(other, rel)) {
                return new Entry(other, rel);
            }
            return new Entry(currentLang, "index.html");
        } catch (Exception ignored) {
            return null;
        }
    }

    private Entry parseAssetUrl(String url) {
        if (url == null || !url.startsWith(ASSET_BASE)) {
            return null;
        }
        String rest = url.substring(ASSET_BASE.length());
        int slash = rest.indexOf('/');
        if (slash < 0) {
            return null;
        }
        String lang = rest.substring(0, slash);
        String path = Uri.decode(rest.substring(slash + 1));
        if (!"zh".equals(lang) && !"en".equals(lang)) {
            return null;
        }
        return new Entry(lang, normalizePath(path));
    }

    private static class Entry {
        final String lang;
        final String path;
        int scrollY;
        Entry(String lang, String path) {
            this(lang, path, 0);
        }
        Entry(String lang, String path, int scrollY) {
            this.lang = lang;
            this.path = path;
            this.scrollY = scrollY;
        }
    }

    private static class PageInfo {
        final String lang;
        final String path;
        final String title;
        final String keywords;
        final String summary;

        PageInfo(String lang, String path, String title, String keywords, String summary) {
            this.lang = lang;
            this.path = path;
            this.title = title;
            this.keywords = keywords == null ? "" : keywords;
            this.summary = summary == null ? "" : summary;
        }

        String searchBlob() {
            return (title + " " + path + " " + keywords + " " + summary).toLowerCase(Locale.ROOT);
        }

        String listLabel() {
            if (summary.length() > 0 && !title.contains(summary)) {
                return title + "\n" + summary + "\n" + path;
            }
            return title + "\n" + path;
        }
    }
}
