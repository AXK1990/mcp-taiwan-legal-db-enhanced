# CHANGELOG

## [1.0.0] - 2026-05-31

基於 [lawchat-oss/mcp-taiwan-legal-db](https://github.com/lawchat-oss/mcp-taiwan-legal-db) 的增強版本

### Added（新增功能）

#### 🌟 簡易案件系統查詢（全新）
- 支援查詢司法院簡易案件系統（地方法院簡易案件、小額案件）
- 可透過 `search_system` 參數選擇：
  - `both` - 同時查詢裁判書系統與簡易案件系統
  - `easy` - 只查詢簡易案件系統
- 自動合併兩個系統的結果並按法院層級排序

#### 🌟 法令判解系統查詢（全新）
- `search_legal_interpretations` - 搜尋司法院法令判解系統
  - 支援大法官解釋、憲法法庭裁判、決議、法律問題、精選裁判、行政函釋等
  - 支援全文關鍵字搜尋（含布林運算符：+、-、&、()）

- `search_legal_interpretations_advanced` - 進階搜尋
  - 支援日期範圍篩選（民國年/月/日格式）
  - 支援文件類型精確篩選
  - 採用兩階段查詢機制（先探索類型，再精確取得）

- `get_legal_interpretation` - 取得法令判解全文
  - 支援所有法令判解類型（決議、法律問題、精選裁判等）

#### 🔧 裁判書搜尋增強
- **分頁支援**
  - 新增 `offset` 參數（可跳過前 N 筆）
  - 配合 `max_results` 可取得最多 500 筆結果
  - 自動解析並回傳真實總筆數（`total_count`）

- **系統選擇機制**
  - 新增 `search_system` 參數：
    - `auto` - 智能判斷（預設）
    - `both` - 雙系統查詢
    - `regular` - 僅裁判書系統
    - `easy` - 僅簡易案件系統

- **件數資訊**
  - `regular_count` - 裁判書系統件數
  - `easy_count` - 簡易案件系統件數
  - 自動提示 500 筆限制並建議解決方案（按時間/法院拆分）

### Changed（改進）
- 移除未使用的 `data.judicial.gov.tw` 域名配置
- 優化查詢效能與錯誤處理

---

## 原專案資訊
- 原專案：[lawchat-oss/mcp-taiwan-legal-db](https://github.com/lawchat-oss/mcp-taiwan-legal-db)
- 授權：MIT License
- 本增強版本由社群開發者維護，與原專案維護者無關
