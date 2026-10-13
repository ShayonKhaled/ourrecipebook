# Our Recipe Book

A small Hugo site built on the [Coyote theme](https://github.com/nightswinger/hugo-theme-coyote).
Every recipe is a card on the home page with its own page, tags, and a Fuse.js
search box.

**Live:** <https://shayonkhaled.github.io/ourrecipebook/>

## Requirements

- Hugo **extended** v0.161 or newer (`hugo version` must say `extended`). The
  theme compiles SCSS, which the non-extended build cannot do.
- Go and Git 1.x are **not** needed - the theme is vendored in `themes/coyote`.

## Run it locally

```bash
hugo server
```

Then open <http://localhost:1313/>.

## Deploying

Deployment is automatic. Pushing to `main` triggers the workflow in
`.github/workflows/hugo.yml`, which builds the site and publishes it to GitHub
Pages.

The workflow passes `--baseURL "${{ steps.pages.outputs.base_url }}/"`, which
GitHub resolves from the repository, so the site works correctly at the
`/ourrecipebook/` subpath and would keep working if it moved to a custom domain
- no edit to `hugo.toml` required.

The `baseURL` in `hugo.toml` is only used for local builds. It is left at a
placeholder, so locally generated absolute links (tag pages, search result
images) will point at that placeholder rather than the live site. Set it to
`https://shayonkhaled.github.io/ourrecipebook/` if you want a local production
build to match live exactly.

To build the output by hand:

```bash
hugo --gc --minify
```

The finished site lands in `public/`.

## Adding a recipe

Recipes are **page bundles**: one folder per recipe, holding the write-up and its
photo together.

```bash
hugo new --kind post-bundle posts/my-new-recipe
```

That creates `content/posts/my-new-recipe/` with an `index.md` (set `draft:
false` when you are ready to publish) and an `image.jpeg`. Drop a real photo in
as `image.jpeg` and it replaces the placeholder card automatically. The card
image renders at a 2:1 ratio, so landscape photos around 1200x600 work best.

Tags drive the tag pages and the search index, so add them in front matter:

```yaml
tags:
  - pasta
  - vegetarian
```

## Layout of this repo

| Path | What it is |
| --- | --- |
| `hugo.toml` | Site config: title, profile block, social link, JSON search output |
| `content/posts/` | One folder per recipe (page bundle) |
| `content/search.md` | The search page, wired to the theme's `search` layout |
| `layouts/` | Small overrides of three theme templates - see below |
| `archetypes/` | Recipe template used by `hugo new` |
| `_tools/make_placeholders.py` | Regenerates the placeholder card images |
| `themes/coyote/` | The theme itself, vendored |

## Why there are files in `layouts/`

The theme is a few years old and Hugo has moved on, so three of its templates are
overridden here rather than patched in place. Keeping the fixes in `layouts/`
means `themes/coyote` can be updated or re-cloned without losing them.

| Override | Why |
| --- | --- |
| `layouts/partials/head.html` | The theme calls `resources.ToCSS`, removed in favour of `css.Sass`. Without this, the build fails and no CSS is emitted. |
| `layouts/_default/single.html` | The theme assumes every page has an `image`, so any page without one (About, ...) crashed with a nil pointer. Image and tags are now optional. |
| `layouts/_default/index.json` | The theme built search-result image URLs as `permalink + image`, which produced a broken `.../about/<nil>` entry for pages with no image. Only pages with a real image are indexed now. |

## Placeholder images

The card images are deliberately plain colour cards with the dish name, meant to
be replaced by real photos. To regenerate them after editing the list in the
script:

```bash
python _tools/make_placeholders.py
```

It needs Pillow (`pip install pillow`). Then copy each generated
`image.jpeg` over the one in the matching recipe folder.
