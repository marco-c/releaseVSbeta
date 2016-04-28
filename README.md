# release-vs-beta graphs
> Graphs to explore the differences between release and beta Firefox populations.

```sh
pip install -r requirements.txt
wget https://analysis-output.telemetry.mozilla.org/beta_release_os_gfx/data/agg_data.tar.gz
bokeh serve --show main.py
```
