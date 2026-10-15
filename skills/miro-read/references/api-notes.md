# API mechanics and coverage

The helper uses Miro REST API v2 directly, without an SDK. Refer to the current [Miro documentation index](https://developers.miro.com/llms.txt) if a documentation URL has moved. Appending `.md` to a Miro documentation page returns its Markdown version where supported.

| Operation | GET endpoint | Pagination |
| --- | --- | --- |
| Discover accessible boards | `/v2/boards` | `offset`, `limit`; search results have a 10,000-board ceiling |
| Board metadata | `/v2/boards/{board_id}` | None |
| Board items | `/v2/boards/{board_id}/items` | `cursor`, `limit=50` |
| One item | `/v2/boards/{board_id}/items/{item_id}` | None |
| Connectors | `/v2/boards/{board_id}/connectors` | `cursor`, `limit=50` |
| Image resource | `data.imageUrl` from an image item | Descriptor or image bytes |

Official references: [boards](https://developers.miro.com/reference/get-boards-1), [items](https://developers.miro.com/reference/get-items-1), [one item](https://developers.miro.com/reference/get-specific-item-1), [connectors](https://developers.miro.com/reference/get-connectors-1), [image item](https://developers.miro.com/reference/get-image-item-1), [authorization](https://developers.miro.com/docs/getting-started-with-oauth).

## What a read establishes

- Complete pagination establishes coverage of the returned API collection, not of every visible board object. Legacy/freehand objects, comments, layers, attachment bodies and unsupported types can be absent or lack text.
- The helper keeps unknown item types and marks non-text/visual content for inspection. A labeled image still requires inspection when its pixels matter.
- Explicit `parent.id` relationships establish frame membership. An item's coordinates may be relative to a parent; global top-to-bottom sorting cannot reconstruct all visual relationships.
- Board reads are not transactional. An actively edited board may change between pages. If that matters, report the retrieval interval and re-read the relevant source items.
- `modifiedAt` records a modification, not approval or semantic supersession. Keep stable IDs and direct source links when comparing versions.
- JSON preserves source text, original content HTML, stable IDs, frame parents, timestamps, geometry, positions and optional connector endpoints/captions. Markdown is a reading view, not a lossless board backup. Item styles, author profiles and unrecognized metadata are not copied.

## Images

Fetch the image item's `data.imageUrl` on the requested board at `api.miro.com`. Current resources use `/v2/boards/{board_id}/resources/{resource_id}`; the helper also accepts the older `/resources/images/{resource_id}` shape. Add `format=original&redirect=false`. If the response is JSON containing a temporary `url`, request that URL without the Authorization header; otherwise use the returned image bytes. Temporary signed links expire and must not be committed or published as stable sources. The permanent item link remains the citation.

The helper intentionally refuses HTTP redirects to avoid forwarding credentials, verifies HTTPS, applies response-size limits and bounded retries, and does not attempt arbitrary attachment scraping. If a CDN requires another redirect or the API returns a different descriptor shape, use an available connected image tool or inspect the item in Miro and state the limitation. Do not claim OCR or visual inspection on the strength of a filename or downloaded file alone.

## Local output

`board.json` is a normalized snapshot with a `coverage` object and explicit limitations. `board.md` groups readable items under their nearest known frame and includes source links. Connectors are fetched only with `--include-connectors`. Images are downloaded only with the explicit `image` command. Board text is never executed, and external links embedded in board text are never automatically followed.
