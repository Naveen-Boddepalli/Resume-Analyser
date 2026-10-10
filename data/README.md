# Data

`data/raw/` is git-ignored. The experiments use a single public benchmark:

* `cnamuangtoun/resume-job-description-fit` on the Hugging Face Hub
  (`train.csv` 53,437,783 bytes, `test.csv` 15,178,234 bytes).
* The Hub page has no dataset card or licence, and the origin of the labels is not documented.
  Treat it as research-only and check provenance before any redistribution.

Fetch it into its own directory (the experiment scripts verify the SHA-256 checksums in
`research/common.py` and refuse to run on altered files):

```bash
mkdir -p data/raw/resume-job-description-fit && cd data/raw/resume-job-description-fit
for f in train.csv test.csv; do
  curl -sSL -o $f "https://huggingface.co/datasets/cnamuangtoun/resume-job-description-fit/resolve/main/$f"
done
```

Never commit resumes or job descriptions to this repository.
