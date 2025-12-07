import json
import os
import re
import shutil
from langchain_community.document_loaders.text import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_core.documents import Document

# 0. 定義持久化路徑
DB_PATH = "./chroma_db"

# 1. 初始化嵌入模型 (本地運行)
# 確保您已經運行了 `ollama pull nomic-embed-text`
print("正在連接到 Ollama 上的 nomic-embed-text 模型...")
try:
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    # 測試連接
    embeddings.embed_query("測試連接")
    print("Ollama 嵌入模型加載完畢。")
except Exception as e:
    print(f"錯誤：無法連接到 Ollama 或加載 'nomic-embed-text' 模型。")
    print(f"請確保 Ollama 正在運行並且您已經執行了 'ollama pull nomic-embed-text'。")
    print(f"詳細錯誤: {e}")
    exit()

# 2. 處理知識庫 A (產品事實)
print("正在加載 KB-A (merged_products.json)...")
with open("./merged_products.json", "r", encoding="utf-8") as f:
    product_entries = json.load(f)

# helper: extract or build a product id
id_re = re.compile(r"\b([A-Z]{1,2}-\d{1,4})\b")

def get_product_id(entry, idx):
    # prefer explicit product_id
    pid = entry.get("product_id")
    if pid:
        return pid
    # try extract from name or product_name
    name = (entry.get("name") or entry.get("product_name") or "")
    m = id_re.search(name)
    if m:
        return m.group(1)
    # fallback: sanitized name or generated id
    if name:
        return re.sub(r"\s+", "_", name)[:60]
    return f"UNK_{idx}"

# 為每個產品生成3個維度的內容chunks
def generate_product_chunks(entry, index):
    """
    為每個產品生成3個chunks：
    1. 基礎信息 (名稱、類別、功能)
    2. 詳細描述和使用場景
    3. 技術規格和特點
    """
    name = entry.get("name") or entry.get("product_name") or ""
    pid = get_product_id(entry, index)
    category = entry.get("category", "")
    features = entry.get("features") or []
    description = entry.get("description", "")
    price = entry.get("price", "")
    
    # 基礎元數據 (所有chunks共用)
    base_metadata = {
        "source": "product_db",
        "product_id": pid,
        "product_name": name,
        "name": name,
        "category": category,
        "price": str(price),
    }
    if features:
        base_metadata["features"] = ", ".join(features)
    if description:
        base_metadata["description"] = description
    
    chunks = []
    
    # ========== CHUNK 1: 基礎信息和功能 ==========
    content_1 = f"產品名稱: {name}\n"
    content_1 += f"產品 ID: {pid}\n"
    content_1 += f"類別: {category}\n"
    content_1 += f"功能: {', '.join(features)}\n"
    if price:
        content_1 += f"價格: {price}"
    
    metadata_1 = {**base_metadata, "chunk_type": "features"}
    chunks.append(Document(page_content=content_1, metadata=metadata_1))
    
    # ========== CHUNK 2: 詳細描述和使用場景 ==========
    # 根據產品類型生成使用場景
    use_cases = generate_use_cases(name, category, features, description)
    content_2 = f"【{name}】\n\n"
    content_2 += f"產品描述：{description}\n\n"
    content_2 += f"適用場景和使用建議：\n"
    for i, use_case in enumerate(use_cases, 1):
        content_2 += f"{i}. {use_case}\n"
    
    metadata_2 = {**base_metadata, "chunk_type": "usecases"}
    chunks.append(Document(page_content=content_2, metadata=metadata_2))
    
    # ========== CHUNK 3: 特徵標籤和技術信息 ==========
    feature_tags = extract_feature_tags(name, category, description, features)
    content_3 = f"產品: {name}\n"
    content_3 += f"特徵標籤: {', '.join(feature_tags)}\n"
    content_3 += f"\n詳細特性：\n"
    for feature in features:
        content_3 += f"• {feature}\n"
    
    metadata_3 = {**base_metadata, "chunk_type": "specs"}
    chunks.append(Document(page_content=content_3, metadata=metadata_3))
    
    return chunks

def extract_feature_tags(name, category, description, features):
    """提取產品的特徵標籤"""
    feature_tags = []
    all_text = (name + " " + category + " " + description + " " + " ".join(features)).lower()
    
    # 防水相關
    if any(w in all_text for w in ["防水", "ipx", "防濕", "耐水", "防潑"]):
        feature_tags.append("防水")
    
    # 藍牙無線
    if any(w in all_text for w in ["藍牙", "bluetooth", "wireless", "無線", "wifi", "wifi 6"]):
        feature_tags.append("藍牙無線")
    
    # 便攜性
    if any(w in all_text for w in ["便攜", "portable", "輕巧", "輕量", "迷你", "小巧"]):
        feature_tags.append("便攜輕巧")
    
    # 音頻設備
    if any(w in all_text for w in ["喇叭", "音箱", "音響", "speaker", "audio", "耳機", "headphone", "earbud", "mic", "麥克風"]):
        feature_tags.append("音頻設備")
    
    # 戶外使用
    if any(w in all_text for w in ["戶外", "outdoor", "海邊", "露營", "派對", "旅行"]):
        feature_tags.append("戶外使用")
    
    # 電池續航
    if any(w in all_text for w in ["電池", "續航", "battery", "endurance", "小時", "天", "充電"]):
        feature_tags.append("電池續航")
    
    # 降噪
    if any(w in all_text for w in ["降噪", "noise", "cancellation", "靜音"]):
        feature_tags.append("降噪")
    
    # 清潔自動化
    if any(w in all_text for w in ["清潔", "掃地", "打掃", "自動", "機器人", "清淨"]):
        feature_tags.append("清潔自動化")
    
    # 健康監測
    if any(w in all_text for w in ["健康", "監測", "監控", "數據", "運動", "體溫", "血氧", "gps", "健身", "睡眠"]):
        feature_tags.append("健康監測")
    
    # 護眼
    if any(w in all_text for w in ["眼睛", "護眼", "藍光", "顯色", "亮度", "無藍光", "srgb"]):
        feature_tags.append("護眼")
    
    # 快充
    if any(w in all_text for w in ["快充", "快速", "充電", "快速充電", "65w", "pd快充", "pd"]):
        feature_tags.append("快速充電")
    
    # 投影
    if any(w in all_text for w in ["投影", "投影機", "放映", "大螢幕", "4k", "分辨率", "resolution"]):
        feature_tags.append("投影")
    
    # 存儲
    if any(w in all_text for w in ["存儲", "硬碟", "ssd", "容量", "速度", "儲存", "檔案", "tb"]):
        feature_tags.append("存儲")
    
    # 舒適性
    if any(w in all_text for w in ["舒適", "舒服", "支撐", "工學", "符合人體", "長時間", "久坐"]):
        feature_tags.append("舒適支撐")
    
    # 智能家居
    if any(w in all_text for w in ["智能", "smart", "app", "遠端", "控制", "自動化", "聯網"]):
        feature_tags.append("智能控制")
    
    return feature_tags

def generate_use_cases(name, category, features, description):
    """根據產品類型和功能生成適用的使用場景"""
    use_cases = []
    all_text = (name + " " + category + " " + description).lower()
    
    # 根據category生成use cases
    if "音頻" in category or "喇叭" in all_text or "耳機" in all_text:
        use_cases.extend([
            "室內聆聽音樂、播放Podcast",
            "戶外派對、野餐、露營時播放音樂",
            "健身房運動時提供節奏感",
            "工作環境中的背景音樂",
        ])
    
    if "家具" in category or "椅" in all_text:
        use_cases.extend([
            "長時間遊戲或工作時的舒適支撐",
            "視訊會議和在家辦公",
            "居家休閒娛樂",
            "符合人體工學的長期使用",
        ])
    
    if "清潔" in all_text or "掃地" in all_text or "機器人" in all_text:
        use_cases.extend([
            "日常自動清潔，解放雙手",
            "家中多個房間的清潔覆蓋",
            "定時排程清潔，維持整潔環境",
            "地板到拖地的一體化解決方案",
        ])
    
    if "穿戴" in category or "手錶" in all_text or "手環" in all_text:
        use_cases.extend([
            "全天候健康數據監測",
            "運動訓練時的數據追蹤",
            "睡眠品質監測和改善",
            "日常活動和步數統計",
        ])
    
    if "投影" in all_text or "家庭娛樂" in category:
        use_cases.extend([
            "客廳電影放映和家庭娛樂",
            "商務會議演示和教學",
            "小空間創造大螢幕體驗",
            "天花板或牆壁投射靈活應用",
        ])
    
    if "儲存" in all_text or "ssd" in all_text or "硬碟" in all_text:
        use_cases.extend([
            "快速傳輸大型視頻和設計檔案",
            "攜帶重要資料進行備份",
            "視頻創作和後製工作流",
            "多設備間的檔案同步",
        ])
    
    if "咖啡" in all_text or "飲品" in all_text:
        use_cases.extend([
            "早晨快速製作高品質咖啡",
            "家庭咖啡館式的咖啡體驗",
            "辦公室快手咖啡製作",
        ])
    
    if "手機" in category or "配件" in category:
        use_cases.extend([
            "出差和旅行時的設備充電",
            "緊急電量救援",
            "多設備同時充電",
        ])
    
    if "鍵盤" in all_text or "滑鼠" in all_text or "電腦周邊" in category:
        use_cases.extend([
            "遊戲競技中的快速反應",
            "長時間辦公和開發工作",
            "精準點擊和文件編輯",
        ])
    
    # 預設使用場景 (如果上面都沒匹配)
    if not use_cases:
        use_cases = [
            "日常生活中的主要使用",
            "滿足特定需求的最佳選擇",
            "提升生活品質的工具",
            "長期使用的理想伴侶",
        ]
    
    return use_cases

# 遍歷所有產品並生成chunks
docs_kb_a = []
for i, entry in enumerate(product_entries, start=1):
    product_chunks = generate_product_chunks(entry, i)
    docs_kb_a.extend(product_chunks)

print(f"KB-A 加載完畢，共 {len(product_entries)} 個產品，生成 {len(docs_kb_a)} 個chunks。")

# 3. 處理知識庫 B (AIO/SEO 規則)
print("正在加載 KB-B (rules.md)...")
loader_kb_b = TextLoader("./rules.md", encoding="utf-8")
rule_docs_raw = loader_kb_b.load()

splitter_kb_b = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs_kb_b = splitter_kb_b.split_documents(rule_docs_raw)

# 為規則文檔添加元數據
for doc in docs_kb_b:
    doc.metadata = {"source": "aio_rules"} # 關鍵元數據
print(f"KB-B 加載完畢，共 {len(docs_kb_b)} 條規則塊。")

# 4. 合併並存儲到 ChromaDB
all_docs = docs_kb_a + docs_kb_b

if os.path.exists(DB_PATH):
    print(f"正在刪除舊的 ChromaDB 目錄: {DB_PATH}")
    shutil.rmtree(DB_PATH)

print("正在創建新的 ChromaDB 向量數據庫 (這可能需要一點時間)...")
vectorstore = Chroma.from_documents(
    documents=all_docs,
    embedding=embeddings,
    persist_directory=DB_PATH
)

print(f"向量數據庫創建完畢，共索引 {len(all_docs)} 個文檔塊。")
print(f"數據庫已保存至: {DB_PATH}")