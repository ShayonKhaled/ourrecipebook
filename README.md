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

There are two ways to add a recipe. The first needs no technical knowledge at
all and is the one to give to anyone who is not comfortable with Git.

### By filling in a web form (no Git, no code)

1. Go to the repo's **Issues** tab and press **New issue**.
2. Choose **New recipe**.
3. Fill in the boxes: name, an optional photo, a sentence about it, ingredients,
   how to make it, and anything worth remembering.
4. Press **Submit new issue**.

That is the whole process. A bot then reads the form, writes the recipe page,
downloads the photo, publishes it, and replies on the issue with a link to the
finished page a couple of minutes later.

What the automation handles so the contributor does not have to:

| Situation | What happens |
| --- | --- |
| No photo attached | A plain card with the recipe name is drawn instead, so the page always has an image |
| Ingredients typed as plain lines | Converted into a proper bulleted list |
| Steps typed without numbers | Numbered automatically (numbers already there are kept) |
| Awkward characters in the name (`'`, `"`, `:`, accents) | Escaped safely, so the site cannot break |
| A recipe with that name already exists | Nothing is published; the issue gets a comment explaining why |
| Name box left empty | The issue gets a comment asking for the name |

The form is defined in `.github/ISSUE_TEMPLATE/new-recipe.yml` and the automation
is `.github/workflows/recipe-from-issue.yml`, which calls
`_tools/recipe_from_issue.py`.

### By hand, in the repository

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
| `layouts/` | Overrides of theme templates - see below |
| `assets/scss/light-only.scss` | Light-only page background, loaded after the theme |
| `archetypes/` | Recipe template used by `hugo new` |
| `.github/ISSUE_TEMPLATE/` | The "New recipe" web form and the New Issue chooser |
| `.github/workflows/` | Publishing the site, and turning form submissions into recipes |
| `_tools/make_placeholders.py` | Regenerates all the placeholder card images |
| `_tools/make_placeholder.py` | Draws one card image, used when a form has no photo |
| `_tools/recipe_from_issue.py` | Turns a filled-in recipe form into a recipe page |
| `_tools/validate_yaml.py` | Checks the workflow and form YAML parses |
| `themes/coyote/` | The theme itself, vendored |

## Light mode only

The site is deliberately light-only; the theme has no dark styling at all.

Two things enforce it:

1. `assets/scss/light-only.scss` paints `html` and `body` white, and sets
   `color-scheme: light`. This matters more than it sounds: the theme never sets
   a page background, so the white was previously just the browser's default
   canvas. A browser is free to repaint a canvas it has no opinion about, which
   is how the site was ending up dark.
2. `layouts/partials/head.html` declares `<meta name="color-scheme" content="light">`
   and the older `supported-color-schemes`.

**Neither can override a browser that force-darkens a page after styling.**
That happens below the CSS layer, so no stylesheet or meta tag can win. In that
case the setting must be turned off in the browser:

| Browser | Setting |
| --- | --- |
| Brave | `brave://flags/#force-dark-mode` -> Disabled (on by default in Brave) |
| Chrome | `chrome://flags/#enable-force-dark` -> Disabled, or turn off "Auto Dark Mode" under Appearance |
| Edge | `edge://flags/#enable-force-dark` -> Disabled |

This is a very common cause of "my site looks dark" on a machine whose OS is set
to dark mode, and it affects any site without a dark variant - not just this one.

## Why there are files in `layouts/`

The theme is a few years old and Hugo has moved on, so three of its templates are
overridden here rather than patched in place. Keeping the fixes in `layouts/`
means `themes/coyote` can be updated or re-cloned without losing them.

| Override | Why |
| --- | --- |
| `layouts/partials/head.html` | The theme calls `resources.ToCSS`, removed in favour of `css.Sass`. Without this, the build fails and no CSS is emitted. Also emits the light-only stylesheet. |
| `layouts/_default/single.html` | The theme assumes every page has an `image`, so any page without one (About, ...) crashed with a nil pointer. Image and tags are now optional. |
| `layouts/_default/summary.html` | The theme dereferenced the card image unconditionally. Because the home page renders every card, **one recipe with a missing photo broke the entire site build**. Now degrades to a plain card. |
| `layouts/_default/list.html` | The theme built tag-page thumbnails as `permalink + image`, which broke for a recipe with no photo. |
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

`_tools/make_placeholder.py` does one recipe at a time and is what the issue-form
workflow uses when a contributor did not attach a photo.

## Checking your changes before pushing

```bash
python _tools/validate_yaml.py      # validates the workflows and issue forms
```

This catches YAML mistakes that would otherwise silently disable a workflow.
It needs PyYAML (`pip install pyyaml`). Note that PyYAML implements YAML 1.1 and
resolves a bare `on:` key to the boolean `True`; the script disables that so
validation matches what GitHub actually does.
