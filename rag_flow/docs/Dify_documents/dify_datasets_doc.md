以下是提取自文件内容的 API 接口信息，整合为 Markdown 格式，从开头到“删除知识库”部分：

# Dify API 文档

## 1. API 服务器信息
- **API 服务器地址**：`https://api.dify.ai/v1`
- **鉴权方式**：使用 API-Key 进行鉴权，建议将 API-Key 存储在后端，避免泄露。
- **鉴权头**：`Authorization: Bearer {API_KEY}`

## 2. 知识库管理

### 2.1 创建空知识库
- **请求方法**：`POST`
- **请求路径**：`/datasets`
- **请求参数**：
  - `name` (string, 必填)：知识库名称
  - `description` (string, 选填)：知识库描述
  - `indexing_technique` (string, 选填)：索引模式，可选值为 `high_quality` 或 `economy`
  - `permission` (string, 选填)：权限设置，默认为 `only_me`，可选值为 `only_me`、`all_team_members` 或 `partial_members`
  - `provider` (string, 选填)：知识库来源，默认为 `vendor`
  - `external_knowledge_api_id` (str, 选填)：外部知识库 API_ID
  - `external_knowledge_id` (str, 选填)：外部知识库 ID
  - `embedding_model` (str, 选填)：Embedding 模型名称
  - `embedding_provider_name` (str, 选填)：Embedding 模型供应商
  - `retrieval_model` (object, 选填)：检索模式配置

### 2.2 知识库列表
- **请求方法**：`GET`
- **请求路径**：`/datasets`
- **查询参数**：
  - `keyword` (string, 可选)：搜索关键词
  - `tag_ids` (array[string], 可选)：标签 ID 列表
  - `page` (integer, 可选)：页码，默认为 1
  - `limit` (string, 可选)：返回条数，默认为 20，范围 1-100
  - `include_all` (boolean, 可选)：是否包含所有数据集（仅对所有者生效），默认为 false

### 2.3 查看知识库详情
- **请求方法**：`GET`
- **请求路径**：`/datasets/{dataset_id}`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID

### 2.4 修改知识库详情
- **请求方法**：`PATCH`
- **请求路径**：`/datasets/{dataset_id}`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
- **请求参数**：
  - `indexing_technique` (string, 选填)：索引模式
  - `permission` (string, 选填)：权限设置
  - `embedding_model_provider` (string, 选填)：嵌入模型提供商
  - `embedding_model` (string, 选填)：嵌入模型
  - `retrieval_model` (object, 选填)：检索参数
  - `partial_member_list` (array, 选填)：部分团队成员 ID 列表

### 2.5 删除知识库
- **请求方法**：`DELETE`
- **请求路径**：`/datasets/{dataset_id}`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID

以下是提取自文件内容的 API 接口信息，从“通过文本更新文档”到“删除文档”部分，整合为 Markdown 格式：

## 3. 文档管理

### 3.1 通过文本更新文档
- **请求方法**：`POST`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}/update-by-text`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID
- **请求参数**：
  - `name` (string, 选填)：文档名称
  - `text` (string, 选填)：文档内容
  - `process_rule` (object, 选填)：处理规则，包括预处理规则、分段规则等

### 3.2 通过文件更新文档
- **请求方法**：`POST`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}/update-by-file`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID
- **请求参数**：
  - `name` (string, 选填)：文档名称
  - `file` (multipart/form-data)：需要上传的文件
  - `process_rule` (object, 选填)：处理规则，包括预处理规则、分段规则等

### 3.3 获取文档嵌入状态（进度）
- **请求方法**：`GET`
- **请求路径**：`/datasets/{dataset_id}/documents/{batch}/indexing-status`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `batch` (string)：上传文档的批次号

### 3.4 删除文档
- **请求方法**：`DELETE`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID

以下是提取自文件内容的 API 接口信息，从“知识库文档列表”到“更新文档子分段”部分，整合为 Markdown 格式：

## 4. 文档管理（续）

### 4.1 知识库文档列表
- **请求方法**：`GET`
- **请求路径**：`/datasets/{dataset_id}/documents`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
- **查询参数**：
  - `keyword` (string, 可选)：搜索关键词，目前仅搜索文档名称
  - `page` (string, 可选)：页码
  - `limit` (string, 可选)：返回条数，默认为 20，范围 1-100

### 4.2 新增分段
- **请求方法**：`POST`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}/segments`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID
- **请求参数**：
  - `segments` (object list)：分段列表，每个分段包含以下字段：
    - `content` (text, 必填)：文本内容或问题内容
    - `answer` (text, 非必填)：答案内容（在 Q&A 模式下需要传值）
    - `keywords` (list, 非必填)：关键字列表

### 4.3 查询文档分段
- **请求方法**：`GET`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}/segments`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID
- **查询参数**：
  - `keyword` (string, 可选)：搜索关键词
  - `status` (string, 可选)：分段状态，例如 `completed`
  - `page` (string, 可选)：页码
  - `limit` (string, 可选)：返回条数，默认为 20，范围 1-100

### 4.4 删除文档分段
- **请求方法**：`DELETE`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID
  - `segment_id` (string)：文档分段 ID

### 4.5 更新文档分段
- **请求方法**：`POST`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID
  - `segment_id` (string)：文档分段 ID
- **请求参数**：
  - `segment` (object)：分段更新内容，包含以下字段：
    - `content` (text, 必填)：文本内容或问题内容
    - `answer` (text, 非必填)：答案内容（在 Q&A 模式下需要传值）
    - `keywords` (list, 非必填)：关键字列表
    - `enabled` (bool, 非必填)：是否启用该分段
    - `regenerate_child_chunks` (bool, 非必填)：是否重新生成子分段

### 4.6 新增文档子分段
- **请求方法**：`POST`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID
  - `segment_id` (string)：分段 ID
- **请求参数**：
  - `content` (string)：子分段内容

### 4.7 查询文档子分段
- **请求方法**：`GET`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID
  - `segment_id` (string)：分段 ID
- **查询参数**：
  - `keyword` (string, 可选)：搜索关键词
  - `page` (integer, 可选)：页码，默认为 1
  - `limit` (integer, 可选)：每页数量，默认为 20，最大为 100

### 4.8 删除文档子分段
- **请求方法**：`DELETE`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID
  - `segment_id` (string)：分段 ID
  - `child_chunk_id` (string)：子分段 ID

### 4.9 更新文档子分段
- **请求方法**：`PATCH`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID
  - `segment_id` (string)：分段 ID
  - `child_chunk_id` (string)：子分段 ID
- **请求参数**：
  - `content` (string)：更新后的子分段内容

以下是提取自文件内容的 API 接口信息，从“获取上传文件”到“获取嵌入模型列表”部分，整合为 Markdown 格式：

## 5. 文件与模型管理

### 5.1 获取上传文件
- **请求方法**：`GET`
- **请求路径**：`/datasets/{dataset_id}/documents/{document_id}/upload-file`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `document_id` (string)：文档 ID

### 5.2 检索知识库
- **请求方法**：`POST`
- **请求路径**：`/datasets/{dataset_id}/retrieve`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
- **请求参数**：
  - `query` (string)：检索关键词
  - `retrieval_model` (object, 选填)：检索参数，包括检索方法、是否启用 Reranking、权重设置等
  - `external_retrieval_model` (object)：外部检索模型配置（目前未启用）

### 5.3 新增元数据
- **请求方法**：`POST`
- **请求路径**：`/datasets/{dataset_id}/metadata`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
- **请求参数**：
  - `type` (string)：元数据类型
  - `name` (string)：元数据名称

### 5.4 更新元数据
- **请求方法**：`PATCH`
- **请求路径**：`/datasets/{dataset_id}/metadata/{metadata_id}`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `metadata_id` (string)：元数据 ID
- **请求参数**：
  - `name` (string)：更新后的元数据名称

### 5.5 删除元数据
- **请求方法**：`DELETE`
- **请求路径**：`/datasets/{dataset_id}/metadata/{metadata_id}`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `metadata_id` (string)：元数据 ID

### 5.6 启用/禁用内置元数据
- **请求方法**：`POST`
- **请求路径**：`/datasets/{dataset_id}/metadata/built-in/{action}`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
  - `action` (string)：操作类型，`enable` 或 `disable`

### 5.7 更新文档元数据
- **请求方法**：`POST`
- **请求路径**：`/datasets/{dataset_id}/documents/metadata`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
- **请求参数**：
  - `operation_data` (object list)：操作数据，包含以下字段：
    - `document_id` (string)：文档 ID
    - `metadata_list` (list)：元数据列表，每个元数据包含以下字段：
      - `id` (string)：元数据 ID
      - `type` (string)：元数据类型
      - `name` (string)：元数据名称
      - `value` (string)：元数据值

### 5.8 查询知识库元数据列表
- **请求方法**：`GET`
- **请求路径**：`/datasets/{dataset_id}/metadata`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID

### 5.9 获取嵌入模型列表
- **请求方法**：`GET`
- **请求路径**：`/workspaces/current/models/model-types/text-embedding`


## 6. 错误信息

错误信息通常以 JSON 格式返回，包含以下字段：

- `code` (string)：错误代码
- `status` (number)：HTTP 状态码
- `message` (string)：错误描述

### 常见错误示例

| 错误代码              | 状态码 | 错误描述                                      |
|-----------------------|--------|-----------------------------------------------|
| `no_file_uploaded`    | 400    | 未上传文件，请上传文件。                       |
| `too_many_files`      | 400    | 仅允许上传一个文件。                           |
| `file_too_large`      | 413    | 文件大小超出限制。                             |
| `unsupported_file_type` | 415    | 文件类型不支持。                               |
| `high_quality_dataset_only` | 400 | 当前操作仅支持高质量（high-quality）数据集。 |
| `dataset_not_initialized` | 400 | 数据集仍在初始化或索引中，请稍后再试。       |
| `archived_document_immutable` | 403 | 归档的文档不可编辑。                         |
| `dataset_name_duplicate` | 409 | 数据集名称已存在，请修改数据集名称。           |
| `invalid_action`      | 400    | 操作无效。                                     |
| `document_already_finished` | 400 | 文档已处理完成，请刷新页面或查看文档详情。   |
| `document_indexing`   | 400    | 文档正在处理中，无法编辑。                     |
| `invalid_metadata`    | 400    | 元数据内容不正确，请检查并验证。               |


## 7. 文档创建

### 7.1 通过文本创建文档
- **请求方法**：`POST`
- **请求路径**：`/datasets/{dataset_id}/document/create-by-text`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
- **请求参数**：
  - `name` (string)：文档名称
  - `text` (string)：文档内容
  - `indexing_technique` (string)：索引方式，可选值为：
    - `high_quality`：高质量，使用 embedding 模型进行嵌入，构建为向量数据库索引
    - `economy`：经济模式，使用 keyword table index 的倒排索引进行构建
  - `doc_form` (string)：索引内容的形式，可选值为：
    - `text_model`：直接对文本进行 embedding
    - `hierarchical_model`：父子结构模式
    - `qa_model`：问答模式，为分片文档生成问答对，然后对问题进行 embedding
  - `doc_language` (string)：在 Q&A 模式下，指定文档的语言，例如 `English` 或 `Chinese`
  - `process_rule` (object)：处理规则，包含以下字段：
    - `mode` (string)：清洗、分段模式，可选值为 `automatic`（自动）或 `custom`（自定义）
    - `rules` (object)：自定义规则（自动模式下为空）
    - `pre_processing_rules` (array[object])：预处理规则，每个规则包含以下字段：
      - `id` (string)：预处理规则的唯一标识符，可选值包括：
        - `remove_extra_spaces`：替换连续空格、换行符、制表符
        - `remove_urls_emails`：删除 URL 和电子邮件地址
      - `enabled` (bool)：是否启用该规则
    - `segmentation` (object)：分段规则，包含以下字段：
      - `separator` (string)：自定义分段标识符，默认为 `\n`
      - `max_tokens` (int)：最大长度（token），默认为 1000
      - `parent_mode` (string)：父分段的召回模式，可选值为 `full-doc`（全文召回）或 `paragraph`（段落召回）
    - `subchunk_segmentation` (object)：子分段规则，包含以下字段：
      - `separator` (string)：分段标识符，默认为 `***`
      - `max_tokens` (int)：最大长度（token），需小于父级长度
      - `chunk_overlap` (int)：分段重叠部分的长度（选填）
  - `retrieval_model` (object)：检索模式，包含以下字段：
    - `search_method` (string)：检索方法，可选值为：
      - `hybrid_search`：混合检索
      - `semantic_search`：语义检索
      - `full_text_search`：全文检索
    - `reranking_enable` (bool)：是否开启 rerank
    - `reranking_model` (object)：Rerank 模型配置，包含以下字段：
      - `reranking_provider_name` (string)：Rerank 模型的提供商
      - `reranking_model_name` (string)：Rerank 模型的名称
    - `top_k` (int)：召回条数
    - `score_threshold_enabled` (bool)：是否开启召回分数限制
    - `score_threshold` (float)：召回分数限制
  - `embedding_model` (string)：Embedding 模型名称
  - `embedding_model_provider` (string)：Embedding 模型供应商

### 7.2 通过文件创建文档
- **请求方法**：`POST`
- **请求路径**：`/datasets/{dataset_id}/document/create-by-file`
- **路径参数**：
  - `dataset_id` (string)：知识库 ID
- **请求参数**：
  - `data` (multipart/form-data json string)：文档配置信息，包含以下字段：
    - `original_document_id` (string, 选填)：源文档 ID，用于重新上传或修改文档清洗、分段配置
    - `indexing_technique` (string)：索引方式，可选值与“通过文本创建文档”一致
    - `doc_form` (string)：索引内容的形式，可选值与“通过文本创建文档”一致
    - `doc_language` (string)：在 Q&A 模式下，指定文档的语言，可选值与“通过文本创建文档”一致
    - `process_rule` (object)：处理规则，结构与“通过文本创建文档”一致
  - `file` (multipart/form-data)：需要上传的文件