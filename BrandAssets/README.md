# TrendHacker — Brand Assets

Logo direction: **03 Rising Hash**. The mark is a hashtag whose right stroke rises into an arrow, standing for trending social posts.

## Colors
| Name | Hex | Use |
|---|---|---|
| Violet (primary) | `#5B3DF5` | Icon tile, "Hacker" in the light lockup, primary buttons |
| Signal Yellow (accent) | `#FFD23F` | The rising arrow, highlights on dark |
| Ink | `#1A1530` | Text, dark backgrounds |
| Mist | `#F3F1FA` | Light backgrounds |
| White | `#FFFFFF` | Strokes on violet or ink |

Don't put yellow on white. It fails contrast, so use violet there.

## Type
**Bricolage Grotesque**, available on Google Fonts. The wordmark uses ExtraBold (800) with −3% tracking, and body text uses 400–500. In every logo SVG the wordmark is outlined, so the font doesn't need to be installed for the logo to render.

## Files
**svg/** (master files, scale freely)
- `logo-horizontal.svg`: primary lockup for light backgrounds
- `logo-horizontal-on-dark.svg`: for ink or dark backgrounds
- `logo-horizontal-mono-black.svg` / `-mono-white.svg`: one-color use, such as print or watermarks
- `wordmark.svg`: text only
- `mark.svg`: violet tile mark, for avatars and profile pictures
- `mark-on-dark.svg` / `mark-on-light.svg` / `mark-mono-*.svg`: mark without the tile
- `app-icon.svg`: rounded app icon. `app-icon-ios.svg` is square because iOS rounds the corners itself. `app-icon-yellow.svg` is an alternate.
- `favicon.svg`: simplified mark for 16–48 px

**png/**: ready-made exports. App icons come at 1024, 512, 192 and 180 (apple-touch). Marks are 512, favicons are 16/32/48, and the lockups are @2x.

**favicon.ico**: 16 + 32 + 48 multi-size.

## Usage
- Clear space around the logo should be at least the height of the "#" crossbar gap, which is about ¼ of the mark's height.
- Minimum sizes are 24 px for the mark (use `favicon.svg` below 32 px) and 120 px wide for the horizontal logo.
- Don't recolor the arrow to match the hash. The rising stroke being a different color is the whole idea.
