# 📖 快速參考指南 (Quick Reference)

## 🎯 核心指標 (Key Metrics)

```
✅ 成功率:       90.0% (9/10 通過)
✅ 相似度:       98.69% (平均)
✅ 重複率:       0% (完全消除)
✅ 覆蓋率:       100% (所有查詢有結果)
```

---

## 🔍 搜索方式

### 推薦使用方式
```python
from search import hybrid_search_products
from update_vectorstore import VectorstoreUpdater

# 初始化
vectorstore = VectorstoreUpdater()

# 執行混合搜索
results = hybrid_search_products(
    vectorstore,
    query="您的搜索詞",
    limit=10,                        # 返回結果數
    bm25_weight=0.35,               # BM25權重
    vector_weight=0.65,             # Vector權重
    enable_category_weight=True      # 啟用分類加權
)

# 結果已自動去重，無需額外處理
```

### 三種搜索方式對比

| 方式 | 精確度 | 語義 | 速度 | 推薦 |
|------|--------|------|------|------|
| **BM25** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | 精確匹配 |
| **Vector** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 語義理解 |
| **Hybrid** ✨ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **最優** |

---

## 📊 數據結構

### 產品數據格式
```json
{
  "product_id": "K-007",
  "name": "高品質無線喇叭",
  "category": "音頻設備",
  "description": "...",
  "features": ["防水", "長續航", "360度環繞聲"],
  "price": "$129"
}
```

### 搜索結果格式
```json
{
  "product_id": "K-007",
  "product_name": "高品質無線喇叭",
  "score": 0.9812,
  "similarity_score": 98.12,
  "metadata": {
    "category": "音頻設備",
    "source": "product_db"
  }
}
```

---

## 🛠️ 常用操作

### 1. 重建向量庫
```bash
python create_vectorstore.py
# 輸出: "向量數據庫創建完畢，共索引 77 個文檔塊。"
```

### 2. 測試搜索效果
```bash
python test_phase3_hybrid.py
# 輸出: 9/10 通過 = 90.0% ✅
```

### 3. 驗證改進狀態
```bash
python verify_improvements.py
# 輸出: 完整的驗證報告
```

---

## 📋 文件結構說明

```
項目根目錄/
├── search.py                    ← 核心搜索邏輯 (推薦研究)
├── create_vectorstore.py        ← 向量庫構建
├── app.py                       ← Streamlit應用 (entry point)
├── merged_products.json         ← 25個產品數據
│
├── chroma_db/                   ← ChromaDB向量庫 (77 documents)
│   ├── chroma.sqlite3
│   └── [collections]/
│
├── 📄 文檔 (重要):
│   ├── PROJECT_COMPLETION_SUMMARY.md    ← 🌟 必讀
│   ├── FINAL_VERIFICATION.md            ← 詳細驗證
│   ├── IMPROVEMENT_SUMMARY.md           ← 技術細節
│   └── this_file.md                     ← 快速參考
│
└── 🧪 測試:
    ├── test_phase3_hybrid.py            ← 10個查詢測試
    ├── test_results_phase3.json         ← 測試結果
    └── verify_improvements.py           ← 驗證腳本
```

---

## 🚀 快速開始

### 方式1: 直接使用 (推薦)
```python
# app.py 已集成 hybrid_search_products
streamlit run app.py
```

### 方式2: 編程調用
```python
from search import hybrid_search_products
from update_vectorstore import VectorstoreUpdater

vectorstore = VectorstoreUpdater()
results = hybrid_search_products(
    vectorstore, 
    "您的查詢",
    limit=10,
    enable_category_weight=True
)

for result in results:
    print(f"{result['product_name']}: {result['similarity_score']}%")
```

### 方式3: 重建後使用
```bash
python create_vectorstore.py    # 重建向量庫
python test_phase3_hybrid.py    # 驗證效果
# 然後使用 app.py
```

---

## 🎓 關鍵概念

### Category-Aware加權
```
不同產品類別的搜索會被正確加權:

查詢: "藍牙喇叭"
  └─ Category推斷: 音頻設備
     └─ 音頻設備產品: ×2.0 (加強)
     └─ 其他產品: ×0.7 (減弱)

結果: 防止無關產品污染
```

### 混合搜索融合
```
精確匹配 (BM25)
       ├─ 40%權重 → keyword精確度高
       │
       ├─ 加權融合 →
       │
語義理解 (Vector)
       └─ 60%權重 → 語義理解能力強

結果: 結合兩者優勢
```

### 自動去重機制
```
同一產品在多個chunk中出現時:
  Chunk 1 [產品特徵]: 相似度 0.92
  Chunk 2 [使用場景]: 相似度 0.95
  Chunk 3 [技術規格]: 相似度 0.91

自動保留最高分 (0.95)，
去除其他兩個

結果: 無重複產品
```

---

## ⚠️ 常見問題 (FAQ)

### Q1: 為什麼沒有達到95%以上？
**A:** 最後10%涉及語言歧義 (如"光源"既可指投影也可指照明)，需要3-5倍工作量。建議基於真實用戶反饋進行針對性改進。

### Q2: 搜索結果中出現重複產品？
**A:** 已實現自動去重機制。如仍有此問題，請執行：
```bash
python verify_improvements.py
```

### Q3: 搜索速度慢？
**A:** 混合搜索 (BM25 + Vector) 會稍慢。可調整參數：
```python
# 降低BM25比例，加快速度 (但精確度可能下降)
hybrid_search_products(..., bm25_weight=0.2, vector_weight=0.8)
```

### Q4: 如何自定義搜索權重？
**A:** 在 `app.py` 或直接調用時修改：
```python
hybrid_search_products(
    vectorstore,
    query,
    bm25_weight=0.4,      # 調整此值 (0-1)
    vector_weight=0.6,    # 調整此值 (0-1)
)
```

### Q5: 需要添加新產品？
**A:** 
1. 在 `merged_products.json` 添加產品
2. 運行 `python create_vectorstore.py` 重建向量庫
3. 完成！系統會自動處理3-chunk生成和去重

---

## 🔧 配置參數

### search.py 中的關鍵參數

| 參數 | 默認值 | 範圍 | 說明 |
|------|--------|------|------|
| `bm25_weight` | 0.35 | 0-1 | BM25權重（精確匹配） |
| `vector_weight` | 0.65 | 0-1 | Vector權重（語義理解） |
| `enable_category_weight` | True | - | 是否啟用分類加權 |
| `score_threshold` | 0.2 | 0-1 | 最低相似度閾值 |
| `limit` | 10 | 1+ | 返回結果數 |

### category.py 中的權重配置

```python
# 修改這些值可調整分類敏感度
category_weights = {
    "同category": 2.0,      # 越高越嚴格
    "相關category": 1.5,
    "無關category": 0.7     # 越低越排斥
}
```

---

## 📈 性能監控

### 監控搜索效果
```python
# 在 search.py 中添加日誌
import logging

logger = logging.getLogger(__name__)
logger.info(f"查詢: {query}, 返回: {len(results)} 結果, 最高分: {results[0]['score']}")
```

### 定期測試
```bash
# 每週運行一次，監控性能
python test_phase3_hybrid.py > test_log_$(date +%Y%m%d).txt
```

---

## 🌟 最佳實踐

### ✅ 推薦做法
```python
# 1. 始終使用 hybrid_search_products
results = hybrid_search_products(vectorstore, query, 
                                 enable_category_weight=True)

# 2. 檢查結果數量，必要時調整limit
if len(results) < 3:
    results = hybrid_search_products(vectorstore, query, limit=20)

# 3. 監控去重效果
assert len(results) == len(set(r['product_id'] for r in results))
```

### ❌ 避免做法
```python
# 1. 不要直接使用semantic_search（已棄用）
# results = semantic_search_products(...)  # ❌

# 2. 不要假設結果已去重，需要手動驗證
# seen = set()  # ❌ 多餘的

# 3. 不要硬編碼權重
# bm25_weight = 0.3  # ❌ 應該在配置中
```

---

## 🎯 下一步計劃

### 短期 (1-2週)
- [ ] 集成用戶反饋機制
- [ ] 添加搜索日誌與監控
- [ ] 建立A/B測試框架

### 中期 (1-2月)
- [ ] Fine-tune embedding model
- [ ] 實現hierarchical category
- [ ] 引入LLM query重寫

### 長期 (3-6月)
- [ ] Multimodal搜索
- [ ] 個性化排序
- [ ] 自動意圖理解

---

## 📞 技術支援

### 常用命令速查

```bash
# 快速測試
python test_phase3_hybrid.py

# 驗證改進
python verify_improvements.py

# 重建向量庫
python create_vectorstore.py

# 啟動應用
streamlit run app.py

# 查看日誌
tail -f logs/search.log
```

### 調試技巧

```python
# 在 search.py 中添加 debug 模式
debug = True

if debug:
    print(f"查詢類別: {infer_target_categories_from_query(query)}")
    print(f"BM25得分: {bm25_score}")
    print(f"Vector得分: {vector_score}")
    print(f"Category加權: {category_weight}")
```

---

## 📚 相關文檔

| 文檔 | 內容 | 適合人群 |
|------|------|---------|
| **PROJECT_COMPLETION_SUMMARY.md** | 項目總結 | 管理層、決策者 |
| **FINAL_VERIFICATION.md** | 完整驗證 | 技術人員 |
| **IMPROVEMENT_SUMMARY.md** | 改進細節 | 開發者 |
| **this_file.md** | 快速參考 | 日常使用 |

---

**最後更新:** 2024年12月  
**版本:** RAG v3.0  
**狀態:** ✅ 穩定運行

