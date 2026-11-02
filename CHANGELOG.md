# Changelog

All notable changes to **pSysmon** (Python System for Seismic Monitoring) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Processing Stack GUI Controls & Node Reordering (`plugins_processingstack.py`)**:
  - Added **Remove**, **Up**, and **Down** buttons to `PStackEditPanel` to allow reordering and removing processing nodes directly within the stack.
  - Implemented index boundary checks and selection tracking when shifting nodes.
  - Added defensive guards against `None` or empty `selected_nodes` preventing `AttributeError: 'NoneType' object has no attribute 'name'` and `TypeError: 'NoneType' object is not iterable`.
- **Enlarged 'Add a processing node' Dialog (`PStackAddNodeDialog`)**:
  - Enlarged dialog dimensions to **880 x 520 px** (minimum size: **860 x 480 px**) and list control to **840 x 360 px**.
  - Sized column widths generously (`name`: 190 px, `mode`: 95 px, `category`: 160 px, `tags`: 380 px) so all processing node names, execution modes, categories, and tags fit comfortably without horizontal truncation.
  - Enabled double-click item activation (`wx.EVT_LIST_ITEM_ACTIVATED`) to immediately select and add a node in one step.
- **Expanded Checklist Box in Processing Stack (`PStackEditPanel`)**:
  - Increased checklist box height to 145–150 px with native auto-scrollbars, allowing all 5 nodes of the optimal processing stack to be viewed simultaneously without manual scrolling.
- **Expanded Node Option Dialog Height (`PStackEditField`)**:
  - Increased default dialog height to 500 px so comprehensive processing nodes (e.g. `remove response (paz)`) display all parameter groups without clipping.
- **`RemoveResponsePAZ` Processing Node**:
  - Implemented the `remove response (paz)` processing node in [`packages/tracedisplay/processingNodes.py`](lib/psysmon/packages/tracedisplay/processingNodes.py).
  - Automatically queries the project's `geometry_inventory` for sensor poles, zeros, sensitivity (<i>A</i><sub>0</sub>, V/(m/s)), and datalogger preamplifier gain and bitweight (V/count).
  - Full GUI preferences interface modeled after `bandpass filter`:
    - Configurable output physical quantity: **Velocity** (`m/s`), **Displacement** (`m`), or **Acceleration** (m/s<sup>2</sup>).
    - 4-corner frequency pre-filter (`pre_filt = [f1, f2, f3, f4]`) with enable/disable toggle to prevent low-frequency noise explosion below geophone eigenfrequencies.
    - Water level regulation in decibels (default 60.0 dB) and cosine tapering controls.
  - Registered as `nodeClass = 'common'`, enabling immediate use in both `ProcessingStackLooperChild` (collection pipelines) and `TraceDisplay` (interactive processing stack).
- **`psysmon_seismic` External Package (SeisMIC Interferometry Integration)**:
  - Integrated the **SeisMIC** ambient noise interferometry and velocity monitoring framework as a modular external pSysmon package located at `psysmon_seismic/`.
  - **`ArrayStackingNode` Processing Node**:
    - Implemented the `array stacking` processing node (`nodeClass = 'common'`) for spatial mini-array beamforming and geophone trace stacking prior to cross-correlation.
    - Operates seamlessly within both `ProcessingStackLooperChild` (batch collection execution) and `TraceDisplay` (interactive visual stack).
    - Supports channel grouping rules (`by_location_code`, `by_station_root`, `all_to_single`), stack mathematical operators (`mean`, `median`, `sum`), output channel modes (`replace`, `replicate`, `append`), and automatic station centroid calculation from `geometry_inventory`.
  - **`SeismicXCorrNode` Collection Child Node**:
    - Implemented `SeisMIC Correlator` child node executing under `TimeWindowLooper`.
    - High-throughput multi-core chunking via `ProcessPoolExecutor` with lock-free HDF5 merging.
    - Zero-disk in-memory waveform injection via `PsysmonStoreClient`.
    - Retains flexibility to process unstacked raw streams directly, with informative user log warnings if constituent geophone channels are detected without upstream stacking.
  - **`SeismicMonitorNode` Collection Node**:
    - Implemented top-level `SeisMIC Monitor` collection node executing Weaver et al. (2011) multi-reference stretching on cross-correlation database pairs.
    - Automatically packages time-dependent velocity variation (&Delta;<i>v</i>/<i>v</i>) measurements into pSysmon's `ResultBag` as both structured CSV tables (`TableResult`) and Python shelve databases (`ShelveResult`).
  - **`SeismicSpatialNode` Collection Node**:
    - Implemented top-level `SeisMIC Spatial` collection node for 2D radiative transfer sensitivity kernel inversion.
    - Exports georeferenced ESRI ASCII raster grids with `.prj` spatial projections (`Grid2dResult`) into the project database.
  - **Full GUI Parameter Exposure (`gui.py`)**:
    - Provided native wxPython tabbed property sheets (`ListbookPrefDialog`) for interactive tuning of all SeisMIC processing and collection parameters.
  - **User & Developer Guide (`SeisMIC_psysmon_guide.md`)**:
    - Authoritative 3-part documentation detailing architecture, complete parameter specifications, and an end-to-end best practice tutorial for the APO23 glacier monitoring dataset.
  - **Automated Integration Test Suite**:
    - Complete test suite in `tests/test_integration.py` covering array stacking, correlation warning logic, result publishing, and end-to-end workflow execution.


### Changed
- **External Package Discovery & Import Paths**:
  - Automatically appended external package root directories and subpackages with `__init__.py` to `sys.path` in both the main process and child workers (`cecSubProcess`), enabling relative and sibling imports across custom packages (commits `21488f9b`, `bb13b8b2`).
- **Inventory XML Loading**:
  - Added support for loading inventory definitions across multiple XML files (commit `61dd5b84`).

### Fixed
- **Processing Stack Preferences Layout Decoupling (`plugins_processingstack.py`)**:
  - Replaced the single `wx.GridBagSizer` with decoupled `wx.BoxSizer` hierarchy (`mainSizer` [vertical] and `topSizer` [horizontal]). Decouples `self.nodeListBox` and control buttons from `self.nodeOptions`, preventing wxWidgets multi-column span deficit redistribution from shrinking the checklist box.
  - Guarantees an identical checklist box width (371 px) and height (145 px) across all processing nodes, perfectly matching `'convert to sensor units'`.
- **Collection Tree Disabled Node Styling & Native Whitish Font Restoration (`collection_panel.py`)**:
  - Implemented color-blind friendly Option B2 styling in `CollectionTreeCtrl`: applies strikethrough typography (`font.SetStrikethrough(True)`), muted grey text (`wx.Colour(178, 178, 178)`), and `node_disabled` icon when disabled.
  - When enabled, resets strikethrough to `False` and restores the theme's native whitish font color using `wx.NullColour` (reverting unintended forced black text).
  - Fixed latent looper child state bug in `refreshCollection()` so individually disabled child nodes are accurately styled as disabled even when the parent looper remains active.
  - Removed unreachable dead code in `onToggleNodeEnable`.
- **`ArrayStackingNode` Checkbox Label Streamlining (`psysmon_seismic/processing_nodes.py`)**:
  - Shortened checkbox label to `'Stacked beam comparison'` to eliminate horizontal layout strain while preserving comprehensive explanations in the tooltip.
- Fixed float values passed into `IntegerSpinPrefItem` and missing `obspy.imaging.cm` imports (commit `22eff701`).
- Fixed Matplotlib artist removal and plot styles for modern Matplotlib releases (commits `d3ea8094`, `20433ff5`).
- Fixed deprecated escape sequences and regex characters (commits `b455b415`, `569869a8`).
- Fixed Python 3.10+ deprecations (`Iterable` moved to `collections.abc`, `getargspec` migration, `np.float` alias removal).
- Modernized packaging and build workflow using `pyproject.toml` (commit `f5b3d14d`).

---

## [0.0.2] - 2025-10-23

### Added
- Core modular architecture decoupling GUI, CLI batch execution (`psysmomat`), and background execution descriptors (`.ced` via `cecSubProcess`).
- `GeometryInventory` object tree supporting stations, channels, sensors, recorders, and automatic UTM reprojection (`get_utm_epsg`).
- Relational database backend via SQLAlchemy with per-project table namespacing.
- Result subsystem publishing typed outputs (`ShelveResult`, `Grid2dResult`, `TableResult`, `JsonResult`).
- Waveform clients supporting `PsysmonDb`, `Earthworm`, and `SeedLink`.
- Stream processing stack with initial nodes: `detrend`, `bandpass filter`, `highpass filter`, `lowpass filter`, `median filter`, `resample`, `scale log10`, and `convert to sensor units`.

---

## [0.0.1] - 2023-05-22

### Added
- Initial public release of pSysmon framework for routine seismological data processing, waveform display, and event management.
