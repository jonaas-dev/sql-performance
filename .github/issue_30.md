## Bug Description

The `view_result` route in `app/routes.py` calls `list_results()` which now returns a tuple `(results, total)` after PR #29, but the route passes it directly as a single value to the template.

## Current Code

```python
@app.route("/results/<result_id>")
def view_result(result_id):
    data = load_result(result_id)
    if data is None:
        return render_template("history.html", results=list_results(), error="Result not found")
```

## Expected Behavior

When accessing `/results/<nonexistent_id>`, the page should display a friendly error message with the history list.

## Actual Behavior

The template receives a tuple instead of a list, causing a 500 Internal Server Error.

## Fix

Unpack the tuple:
```python
results, _ = list_results()
return render_template("history.html", results=results, error="Result not found")
```

## Acceptance Criteria

- [ ] Accessing `/results/nonexistent` returns status 200 with error message
- [ ] Existing functionality for valid result IDs remains unchanged
