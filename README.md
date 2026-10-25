# Yokubi 

Yokubi is a Japanese grammar guide for beginners and new learners.

View the project at [yoku.bi](https://yoku.bi).

Contribute by joining our [discord community](https://discord.gg/KZj4dVFDzu)
## Building

The book is available in English (`src/`) and Simplified Chinese (`zh/src/`). Build both with:

```sh
./scripts/build.sh
```

This writes the English book to `book/html/` and the Chinese book to `book/html/zh/`. Both editions share the same file layout, so the language switcher in the menu bar keeps readers on the same page. When adding or renaming a lesson, update both `src/` and `zh/src/` (including `SUMMARY.md`).

`./scripts/export-remarkable.sh` exports both editions as light-theme PDFs sized for the reMarkable 2 screen, to `book/remarkable/yokubi-en.pdf` and `yokubi-zh.pdf`. It needs mdbook and Google Chrome, and uses macOS fonts. The deploy workflow exports them on a macOS runner, keeps them as the `yokubi-remarkable` artifact, and publishes them next to the site, where the front page links to them.
