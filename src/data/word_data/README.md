
# add source column

```python
import pandas as pd
df = pd.read_csv(f'eiken_derujun_added.csv')
df["source"] = "derujun"
df.to_csv(f'eiken_derujun_added.csv', index=False)
```
