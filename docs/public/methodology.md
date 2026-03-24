# Methodology / Metodologia

This public site is generated from Phase 2 report artifacts, not from direct raw-source reads. / Este sitio publico se genera a partir de artefactos de la fase 2 y no desde lecturas directas de las fuentes crudas.

## Pipeline / Pipeline
- Upstream source data is normalized into curated DuckDB and Parquet outputs. / Los datos fuente se normalizan a salidas curadas en DuckDB y Parquet.
- Closed weekly and monthly report artifacts are generated from curated storage. / Los artefactos semanales y mensuales se generan a partir del almacenamiento curado.
- Phase 3 copies only public-safe CSV downloads and HTML report snapshots into the public site source. / La fase 3 copia solo descargas CSV seguras para publico y snapshots HTML al sitio publico.

## Public boundary / Limite publico
- Row-level public downloads exclude company, URL, raw descriptions, raw job IDs, and raw OpenAI payloads. / Las descargas publicas excluyen empresa, URL, descripciones crudas, IDs de vacante crudos y payloads crudos de OpenAI.
- Aggregate report content may reference company names only in aggregated ranking sections. / El contenido agregado puede mencionar empresas solo en rankings agregados.
- Private drill-down remains local-only in the Streamlit app. / El detalle privado solo vive localmente en la app de Streamlit.
