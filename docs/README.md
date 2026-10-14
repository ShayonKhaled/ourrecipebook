# Our Recipe Book

<https://shayonkhaled.github.io/ourrecipebook/>

Hugo site using the [Coyote theme](https://github.com/nightswinger/hugo-theme-coyote).

## Local

Needs Hugo extended 0.161 or newer.

```bash
hugo server
```

## Adding a recipe

Open an issue using the **New recipe** form. Fill in the boxes and submit. A
workflow writes the page, publishes it, and closes the issue with a link. If no
photo is attached, a placeholder card is drawn from the recipe name.

**Setup:** the workflow needs a `RECIPE_PUSH_TOKEN` secret - a personal access
token with `repo` scope.

## By hand

```bash
hugo new --kind post-bundle posts/my-recipe
```

Each recipe is a page bundle: one folder under `content/posts/` with an
`index.md` and an `image.jpeg`. Landscape photos around 1200x600 work best.

## Deploying

Push to `main`. The workflow builds and publishes to GitHub Pages.

## Layout overrides

`layouts/` overrides theme templates that are broken with current Hugo:

| File | Why |
| --- | --- |
| `partials/head.html` | Theme used `resources.ToCSS`, removed in favour of `css.Sass` |
| `_default/single.html` | Theme assumed every page has an image |
| `_default/summary.html` | A missing image broke the whole build |
| `_default/list.html` | Thumbnail URL broke without an image |
| `_default/index.json` | Emitted a broken `<nil>` image URL for pages without one |
