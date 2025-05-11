以下是将文件内容整合为清晰的Markdown格式的API文档：

# Dify CHATFLOW API 文档

## 基础信息

- **基础 URL**：`https://api.dify.ai/v1`
- **鉴权方式**：使用 API-Key，通过 `Authorization` HTTP Header 传递，格式为 `Bearer {API_KEY}`。

## API 接口

### 1. 对话消息

#### 1.1 发送对话消息

- **请求方法**：`POST /chat-messages`
- **请求参数**：
  - `query` (string)：用户输入/提问内容。
  - `inputs` (object)：允许传入 App 定义的各变量值。
  - `response_mode` (string)：响应模式，`streaming`（流式模式）或 `blocking`（阻塞模式）。
  - `user` (string)：用户标识。
  - `conversation_id` (string)：会话 ID（选填）。
  - `files` (array[object])：文件列表，支持多种文件类型。
  - `auto_generate_name` (bool)：是否自动生成标题（选填，默认 `true`）。
- **返回内容**：
  - 阻塞模式：返回 `ChatCompletionResponse` 对象。
  - 流式模式：返回 `ChunkChatCompletionResponse` 流式序列。

#### 1.2 停止响应

- **请求方法**：`POST /chat-messages/:task_id/stop`
- **请求参数**：
  - `task_id` (string)：任务 ID。
  - `user` (string)：用户标识。
- **返回内容**：
  - 固定返回 `{"result": "success"}`。

### 2. 文件上传

- **请求方法**：`POST /files/upload`
- **请求参数**：
  - `file` (file)：要上传的文件。
  - `user` (string)：用户标识。
- **返回内容**：
  - 返回文件的 ID 和相关信息。

### 3. 消息反馈

- **请求方法**：`POST /messages/:message_id/feedbacks`
- **请求参数**：
  - `message_id` (string)：消息 ID。
  - `rating` (string)：点赞（`like`）、点踩（`dislike`）或撤销点赞（`null`）。
  - `user` (string)：用户标识。
  - `content` (string)：反馈的具体信息。
- **返回内容**：
  - 固定返回 `{"result": "success"}`。

### 4. 获取下一轮建议问题列表

- **请求方法**：`GET /messages/{message_id}/suggested`
- **请求参数**：
  - `message_id` (string)：消息 ID。
  - `user` (string)：用户标识。
- **返回内容**：
  - 返回建议问题列表。

### 5. 获取会话历史消息

- **请求方法**：`GET /messages`
- **请求参数**：
  - `conversation_id` (string)：会话 ID。
  - `user` (string)：用户标识。
  - `first_id` (string)：当前页第一条聊天记录的 ID（选填）。
  - `limit` (int)：一次请求返回的聊天记录条数（默认 20 条）。
- **返回内容**：
  - 返回历史消息列表。

### 6. 获取会话列表

- **请求方法**：`GET /conversations`
- **请求参数**：
  - `user` (string)：用户标识。
  - `last_id` (string)：当前页最后一条记录的 ID（选填）。
  - `limit` (int)：一次请求返回的记录条数（默认 20 条，最大 100 条）。
  - `sort_by` (string)：排序字段（默认 `-updated_at`）。
- **返回内容**：
  - 返回会话列表。

### 7. 删除会话

- **请求方法**：`DELETE /conversations/:conversation_id`
- **请求参数**：
  - `conversation_id` (string)：会话 ID。
  - `user` (string)：用户标识。
- **返回内容**：
  - 固定返回 `{"result": "success"}`。

### 8. 会话重命名

- **请求方法**：`POST /conversations/:conversation_id/name`
- **请求参数**：
  - `conversation_id` (string)：会话 ID。
  - `name` (string)：会话名称（选填）。
  - `auto_generate` (bool)：是否自动生成标题（选填，默认 `false`）。
  - `user` (string)：用户标识。
- **返回内容**：
  - 返回会话的详细信息。

### 9. 获取对话变量

- **请求方法**：`GET /conversations/:conversation_id/variables`
- **请求参数**：
  - `conversation_id` (string)：会话 ID。
  - `user` (string)：用户标识。
  - `last_id` (string)：当前页最后一条记录的 ID（选填）。
  - `limit` (int)：一次请求返回的记录条数（默认 20 条，最大 100 条）。
- **返回内容**：
  - 返回变量列表。

### 10. 语音转文字

- **请求方法**：`POST /audio-to-text`
- **请求参数**：
  - `file` (file)：语音文件。
  - `user` (string)：用户标识。
- **返回内容**：
  - 返回转换后的文字内容。

### 11. 文字转语音

- **请求方法**：`POST /text-to-audio`
- **请求参数**：
  - `message_id` (str)：Dify 生成的文本消息 ID（选填）。
  - `text` (str)：语音生成内容（选填）。
  - `user` (string)：用户标识。
- **返回内容**：
  - 返回语音文件。

### 12. 获取应用基本信息

- **请求方法**：`GET /info`
- **返回内容**：
  - 返回应用的基本信息，包括名称、描述和标签。

### 13. 获取应用参数

- **请求方法**：`GET /parameters`
- **返回内容**：
  - 返回应用的功能开关、输入参数名称、类型及默认值等信息。

### 14. 获取应用 Meta 信息

- **请求方法**：`GET /meta`
- **返回内容**：
  - 返回应用的工具图标等 Meta 信息。

### 15. 获取标注列表

- **请求方法**：`GET /apps/annotations`
- **请求参数**：
  - `page` (string)：页码。
  - `limit` (string)：每页数量。
- **返回内容**：
  - 返回标注列表。

### 16. 创建标注

- **请求方法**：`POST /apps/annotations`
- **请求参数**：
  - `question` (string)：问题。
  - `answer` (string)：答案内容。
- **返回内容**：
  - 返回创建的标注信息。

### 17. 更新标注

- **请求方法**：`PUT /apps/annotations/{annotation_id}`
- **请求参数**：
  - `annotation_id` (string)：标注 ID。
  - `question` (string)：问题。
  - `answer` (string)：答案内容。
- **返回内容**：
  - 返回更新后的标注信息。

### 18. 删除标注

- **请求方法**：`DELETE /apps/annotations/{annotation_id}`
- **请求参数**：
  - `annotation_id` (string)：标注 ID。
- **返回内容**：
  - 固定返回 `{"result": "success"}`。

### 19. 标注回复初始设置

- **请求方法**：`POST /apps/annotation-reply/{action}`
- **请求参数**：
  - `action` (string)：动作，`enable` 或 `disable`。
  - `embedding_provider_name` (string)：嵌入模型提供商名称。
  - `embedding_model_name` (string)：嵌入模型名称。
  - `score_threshold` (number)：相似度阈值。
- **返回内容**：
  - 返回任务 ID 和状态。

### 20. 查询标注回复初始设置任务状态

- **请求方法**：`GET /apps/annotation-reply/{action}/status/{job_id}`
- **请求参数**：
  - `action` (string)：动作，`enable` 或 `disable`。
  - `job_id` (string)：任务 ID。
- **返回内容**：
  - 返回任务的状态和相关信息。


### 21. 查询标注回复初始设置任务状态

- **请求方法**：`GET /apps/annotation-reply/{action}/status/{job_id}`
- **请求参数**：
  - `action` (string)：动作，`enable` 或 `disable`。
  - `job_id` (string)：任务 ID。
- **返回内容**：
  - 返回任务的状态和相关信息。

---

## 错误码

- **400**：
  - `invalid_param`：传入参数异常。
  - `app_unavailable`：App 配置不可用。
  - `provider_not_initialize`：无可用模型凭据配置。
  - `provider_quota_exceeded`：模型调用额度不足。
  - `model_currently_not_support`：当前模型不可用。
  - `completion_request_error`：文本生成失败。
  - `no_file_uploaded`：必须提供文件。
  - `too_many_files`：目前只接受一个文件。
  - `unsupported_preview`：该文件不支持预览。
  - `unsupported_estimate`：该文件不支持估算。
  - `file_too_large`：文件太大。
  - `unsupported_file_type`：不支持的扩展名。
  - `s3_connection_failed`：无法连接到 S3 服务。
  - `s3_permission_denied`：无权限上传文件到 S3。
  - `s3_file_too_large`：文件超出 S3 大小限制。
- **404**：
  - `conversation_not_exists`：对话不存在。
- **500**：服务内部异常。

---

## 附录

### 文件类型支持

- **文档类型**：`TXT`, `MD`, `MARKDOWN`, `PDF`, `HTML`, `XLSX`, `XLS`, `DOCX`, `CSV`, `EML`, `MSG`, `PPTX`, `PPT`, `XML`, `EPUB`
- **图片类型**：`JPG`, `JPEG`, `PNG`, `GIF`, `WEBP`, `SVG`
- **音频类型**：`MP3`, `M4A`, `WAV`, `WEBM`, `AMR`
- **视频类型**：`MP4`, `MOV`, `MPEG`, `MPGA`

### 响应模式

- **流式模式（`streaming`）**：基于 SSE（Server-Sent Events）实现类似打字机输出方式的流式返回。
- **阻塞模式（`blocking`）**：等待执行完毕后返回结果。由于 Cloudflare 限制，请求会在 100 秒超时无返回后中断。


# 工作流编排对话型应用 API

对话应用支持会话持久化，可将之前的聊天记录作为上下文进行回答，可适用于聊天/客服 AI 等。

## 基础 URL

```
http://124.71.148.16/v1
```

## 鉴权

Service API 使用 API-Key 进行鉴权。强烈建议开发者把 API-Key 放在后端存储，而非分享或者放在客户端存储，以免 API-Key 泄露，导致财产损失。所有 API 请求都应在 Authorization HTTP Header 中包含您的 API-Key，如下所示：

```
Authorization: Bearer {API_KEY}
```

---

## API Endpoints

### POST /chat-messages
**发送对话消息**  
创建会话消息。

#### Request Body
| Name | Type | Description |
|------|------|-------------|
| query | string | 用户输入/提问内容 |
| inputs | object | 允许传入 App 定义的各变量值。inputs 参数包含了多组键值对（Key/Value pairs），每组的键对应一个特定变量，每组的值则是该变量的具体值。如果变量是文件类型，请指定一个包含以下 files 中所述键的对象。默认 {} |
| response_mode | string | `streaming` 流式模式（推荐）。基于 SSE（Server-Sent Events）实现类似打字机输出方式的流式返回。<br>`blocking` 阻塞模式，等待执行完毕后返回结果。（请求若流程较长可能会被中断）。由于 Cloudflare 限制，请求会在 100 秒超时无返回后中断。 |
| user | string | 用户标识，用于定义终端用户的身份，方便检索、统计。由开发者定义规则，需保证用户标识在应用内唯一。 |
| conversation_id | string | （选填）会话 ID，需要基于之前的聊天记录继续对话，必须传之前消息的 conversation_id。 |
| files | array[object] | 文件列表，适用于传入文件结合文本理解并回答问题，仅当模型支持 Vision 能力时可用。<br>- `type` (string) 支持类型：<br>  - document: 'TXT', 'MD', 'MARKDOWN', 'PDF', 'HTML', 'XLSX', 'XLS', 'DOCX', 'CSV', 'EML', 'MSG', 'PPTX', 'PPT', 'XML', 'EPUB'<br>  - image: 'JPG', 'JPEG', 'PNG', 'GIF', 'WEBP', 'SVG'<br>  - audio: 'MP3', 'M4A', 'WAV', 'WEBM', 'AMR'<br>  - video: 'MP4', 'MOV', 'MPEG', 'MPGA'<br>  - custom: 其他文件类型<br>- `transfer_method` (string) 传递方式:<br>  - remote_url: 图片地址<br>  - local_file: 上传文件<br>- `url` 图片地址（仅当传递方式为 remote_url 时）<br>- `upload_file_id` 上传文件 ID（仅当传递方式为 local_file 时） |
| auto_generate_name | bool | （选填）自动生成标题，默认 true。若设置为 false，则可通过调用会话重命名接口并设置 auto_generate 为 true 实现异步生成标题。 |

#### Response
当 `response_mode` 为 `blocking` 时，返回 `ChatCompletionResponse` object。  
当 `response_mode` 为 `streaming` 时，返回 `ChunkChatCompletionResponse` object 流式序列。

**ChatCompletionResponse**  
返回完整的 App 结果，Content-Type 为 application/json。
- event (string) 事件类型，固定为 message
- task_id (string) 任务 ID，用于请求跟踪和下方的停止响应接口
- id (string) 唯一ID
- message_id (string) 消息唯一 ID
- conversation_id (string) 会话 ID
- mode (string) App 模式，固定为 chat
- answer (string) 完整回复内容
- metadata (object) 元数据
- usage (Usage) 模型用量信息
- retriever_resources (array[RetrieverResource]) 引用和归属分段列表
- created_at (int) 消息创建时间戳，如：1705395332

**ChunkChatCompletionResponse**  
返回 App 输出的流式块，Content-Type 为 text/event-stream。每个流式块均为 `data:` 开头，块之间以 `\n\n` 即两个换行符分隔。

流式块中根据 event 不同，结构也不同：

| Event | Description | Fields |
|-------|-------------|--------|
| message | LLM 返回文本块事件 | - task_id (string)<br>- message_id (string)<br>- conversation_id (string)<br>- answer (string)<br>- created_at (int) |
| message_file | 文件事件，表示有新文件需要展示 | - id (string)<br>- type (string) 文件类型，目前仅为image<br>- belongs_to (string) 文件归属，user或assistant<br>- url (string) 文件访问地址<br>- conversation_id (string) |
| message_end | 消息结束事件 | - task_id (string)<br>- message_id (string)<br>- conversation_id (string)<br>- metadata (object)<br>- usage (Usage)<br>- retriever_resources (array[RetrieverResource]) |
| tts_message | TTS 音频流事件 | - task_id (string)<br>- message_id (string)<br>- audio (string) Base64编码的音频<br>- created_at (int) |
| tts_message_end | TTS 音频流结束事件 | - task_id (string)<br>- message_id (string)<br>- audio (string) 空字符串<br>- created_at (int) |
| message_replace | 消息内容替换事件 | - task_id (string)<br>- message_id (string)<br>- conversation_id (string)<br>- answer (string) 替换内容<br>- created_at (int) |
| workflow_started | workflow 开始执行 | - task_id (string)<br>- workflow_run_id (string)<br>- event (string) 固定为 workflow_started<br>- data (object) 详细内容 |
| node_started | node 开始执行 | - task_id (string)<br>- workflow_run_id (string)<br>- event (string) 固定为 node_started<br>- data (object) 详细内容 |
| node_finished | node 执行结束 | - task_id (string)<br>- workflow_run_id (string)<br>- event (string) 固定为 node_finished<br>- data (object) 详细内容 |
| workflow_finished | workflow 执行结束 | - task_id (string)<br>- workflow_run_id (string)<br>- event (string) 固定为 workflow_finished<br>- data (object) 详细内容 |
| error | 流式输出过程中出现的异常 | - task_id (string)<br>- message_id (string)<br>- status (int) HTTP 状态码<br>- code (string) 错误码<br>- message (string) 错误消息 |
| ping | 每 10s 一次的 ping 事件 | - |

#### Errors
- 404: 对话不存在
- 400: invalid_param - 传入参数异常
- 400: app_unavailable - App 配置不可用
- 400: provider_not_initialize - 无可用模型凭据配置
- 400: provider_quota_exceeded - 模型调用额度不足
- 400: model_currently_not_support - 当前模型不可用
- 400: completion_request_error - 文本生成失败
- 500: 服务内部异常

---

### POST /files/upload
**上传文件**  
上传文件并在发送消息时使用，可实现图文多模态理解。支持您的应用程序所支持的所有格式。上传的文件仅供当前终端用户使用。

#### Request Body
该接口需使用 multipart/form-data 进行请求。

| Name | Type | Description |
|------|------|-------------|
| file | file | 要上传的文件 |
| user | string | 用户标识，必须和发送消息接口传入 user 保持一致 |

#### Response
- id (uuid) ID
- name (string) 文件名
- size (int) 文件大小（byte）
- extension (string) 文件后缀
- mime_type (string) 文件 mime-type
- created_by (uuid) 上传人 ID
- created_at (timestamp) 上传时间

#### Errors
- 400: no_file_uploaded - 必须提供文件
- 400: too_many_files - 目前只接受一个文件
- 400: unsupported_preview - 该文件不支持预览
- 400: unsupported_estimate - 该文件不支持估算
- 413: file_too_large - 文件太大
- 415: unsupported_file_type - 不支持的扩展名
- 503: s3_connection_failed - 无法连接到 S3 服务
- 503: s3_permission_denied - 无权限上传文件到 S3
- 503: s3_file_too_large - 文件超出 S3 大小限制

---

### POST /chat-messages/:task_id/stop
**停止响应**  
仅支持流式模式。

#### Path
- task_id (string) 任务 ID，可在流式返回 Chunk 中获取

#### Request Body
- user (string) Required 用户标识，必须和发送消息接口传入 user 保持一致

#### Response
- result (string) 固定返回 success

---

### POST /messages/:message_id/feedbacks
**消息反馈（点赞）**  
消息终端用户反馈、点赞，方便应用开发者优化输出预期。

#### Path Params
| Name | Type | Description |
|------|------|-------------|
| message_id | string | 消息 ID |

#### Request Body
| Name | Type | Description |
|------|------|-------------|
| rating | string | 点赞 like, 点踩 dislike, 撤销点赞 null |
| user | string | 用户标识，需保证用户标识在应用内唯一 |
| content | string | 消息反馈的具体信息 |

#### Response
- result (string) 固定返回 success

---

### GET /messages/{message_id}/suggested
**获取下一轮建议问题列表**

#### Path Params
| Name | Type | Description |
|------|------|-------------|
| message_id | string | Message ID |

#### Query
| Name | Type | Description |
|------|------|-------------|
| user | string | 用户标识，需保证用户标识在应用内唯一 |

---

### GET /messages
**获取会话历史消息**  
滚动加载形式返回历史聊天记录，第一页返回最新 limit 条，即：倒序返回。

#### Query
| Name | Type | Description |
|------|------|-------------|
| conversation_id | string | 会话 ID |
| user | string | 用户标识 |
| first_id | string | 当前页第一条聊天记录的 ID，默认 null |
| limit | int | 一次请求返回多少条聊天记录，默认 20 条 |

#### Response
- data (array[object]) 消息列表
  - id (string) 消息 ID
  - conversation_id (string) 会话 ID
  - inputs (object) 用户输入参数
  - query (string) 用户输入 / 提问内容
  - message_files (array[object]) 消息文件
    - id (string) ID
    - type (string) 文件类型，image 图片
    - url (string) 预览图片地址
    - belongs_to (string) 文件归属方，user 或 assistant
  - answer (string) 回答消息内容
  - created_at (timestamp) 创建时间
  - feedback (object) 反馈信息
    - rating (string) 点赞 like / 点踩 dislike
  - retriever_resources (array[RetrieverResource]) 引用和归属分段列表
- has_more (bool) 是否存在下一页
- limit (int) 返回条数

---

### GET /conversations
**获取会话列表**  
获取当前用户的会话列表，默认返回最近的 20 条。

#### Query
| Name | Type | Description |
|------|------|-------------|
| user | string | 用户标识 |
| last_id | string | （选填）当前页最后面一条记录的 ID，默认 null |
| limit | int | （选填）一次请求返回多少条记录，默认 20 条，最大 100 条，最小 1 条 |
| sort_by | string | （选填）排序字段，默认 -updated_at(按更新时间倒序排列)<br>可选值：created_at, -created_at, updated_at, -updated_at |

#### Response
- data (array[object]) 会话列表
  - id (string) 会话 ID
  - name (string) 会话名称
  - inputs (object) 用户输入参数
  - status (string) 会话状态
  - introduction (string) 开场白
  - created_at (timestamp) 创建时间
  - updated_at (timestamp) 更新时间
- has_more (bool)
- limit (int) 返回条数

---

### DELETE /conversations/:conversation_id
**删除会话**

#### Path
- conversation_id (string) 会话 ID

#### Request Body
| Name | Type | Description |
|------|------|-------------|
| user | string | 用户标识 |

#### Response
- result (string) 固定返回 success

---

### POST /conversations/:conversation_id/name
**会话重命名**  
对会话进行重命名，会话名称用于显示在支持多会话的客户端上。

#### Path
- conversation_id (string) 会话 ID

#### Request Body
| Name | Type | Description |
|------|------|-------------|
| name | string | （选填）名称，若 auto_generate 为 true 时，该参数可不传 |
| auto_generate | bool | （选填）自动生成标题，默认 false |
| user | string | 用户标识 |

#### Response
- id (string) 会话 ID
- name (string) 会话名称
- inputs (object) 用户输入参数
- status (string) 会话状态
- introduction (string) 开场白
- created_at (timestamp) 创建时间
- updated_at (timestamp) 更新时间

---

### GET /conversations/:conversation_id/variables
**获取对话变量**  
从特定对话中检索变量。此端点对于提取对话过程中捕获的结构化数据非常有用。

#### 路径参数
| Name | Type | Description |
|------|------|-------------|
| conversation_id | string | 要从中检索变量的对话ID |

#### 查询参数
| Name | Type | Description |
|------|------|-------------|
| user | string | 用户标识符 |
| last_id | string | （选填）当前页最后面一条记录的 ID，默认 null |
| limit | int | （选填）一次请求返回多少条记录，默认 20 条 |

#### 响应
- limit (int) 每页项目数
- has_more (bool) 是否有更多项目
- data (array[object]) 变量列表
  - id (string) 变量ID
  - name (string) 变量名称
  - value_type (string) 变量类型
  - value (string) 变量值
  - description (string) 变量描述
  - created_at (int) 创建时间戳
  - updated_at (int) 最后更新时间戳

#### 错误
- 404: conversation_not_exists - 对话不存在

---

### POST /audio-to-text
**语音转文字**

#### Request Body
该接口需使用 multipart/form-data 进行请求。

| Name | Type | Description |
|------|------|-------------|
| file | file | 语音文件。支持格式：['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'] 文件大小限制：15MB |
| user | string | 用户标识 |

#### Response
- text (string) 输出文字

---

### POST /text-to-audio
**文字转语音**

#### Request Body
| Name | Type | Description |
|------|------|-------------|
| message_id | str | Dify 生成的文本消息，优先使用 |
| text | str | 语音生成内容 |
| user | string | 用户标识 |

---

### GET /info
**获取应用基本信息**

#### Response
- name (string) 应用名称
- description (string) 应用描述
- tags (array[string]) 应用标签

---

### GET /parameters
**获取应用参数**  
用于进入页面一开始，获取功能开关、输入参数名称、类型及默认值等使用。

#### Response
- opening_statement (string) 开场白
- suggested_questions (array[string]) 开场推荐问题列表
- suggested_questions_after_answer (object) 启用回答后给出推荐问题
  - enabled (bool) 是否开启
- speech_to_text (object) 语音转文本
  - enabled (bool) 是否开启
- retriever_resource (object) 引用和归属
  - enabled (bool) 是否开启
- annotation_reply (object) 标记回复
  - enabled (bool) 是否开启
- user_input_form (array[object]) 用户输入表单配置
  - text-input (object) 文本输入控件
    - label (string) 控件展示标签名
    - variable (string) 控件 ID
    - required (bool) 是否必填
    - default (string) 默认值
  - paragraph (object) 段落文本输入控件
    - label (string) 控件展示标签名
    - variable (string) 控件 ID
    - required (bool) 是否必填
    - default (string) 默认值
  - select (object) 下拉控件
    - label (string) 控件展示标签名
    - variable (string) 控件 ID
    - required (bool) 是否必填
    - default (string) 默认值
    - options (array[string]) 选项值
  - file_upload (object) 文件上传配置
    - image (object) 图片设置
      - enabled (bool) 是否开启
      - number_limits (int) 图片数量限制，默认 3
      - transfer_methods (array[string]) 传递方式列表，remote_url , local_file
- system_parameters (object) 系统参数
  - file_size_limit (int) Document upload size limit (MB)
  - image_file_size_limit (int) Image file upload size limit (MB)
  - audio_file_size_limit (int) Audio file upload size limit (MB)
  - video_file_size_limit (int) Video file upload size limit (MB)

---

### GET /meta
**获取应用Meta信息**  
用于获取工具icon

#### Response
- tool_icons(object[string]) 工具图标
  - 工具名称 (string)
    - icon (object|string)
      - (object) 图标
        - background (string) hex格式的背景色
        - content(string) emoji
      - (string) 图标URL

---

### GET /apps/annotations
**获取标注列表**

#### Query
| Name | Type | Description |
|------|------|-------------|
| page | string | 页码 |
| limit | string | 每页数量 |

---

### POST /apps/annotations
**创建标注**

#### Query
| Name | Type | Description |
|------|------|-------------|
| question | string | 问题 |
| answer | string | 答案内容 |

---

### PUT /apps/annotations/{annotation_id}
**更新标注**

#### Query
| Name | Type | Description |
|------|------|-------------|
| annotation_id | string | 标注 ID |
| question | string | 问题 |
| answer | string | 答案内容 |

---

### DELETE /apps/annotations/{annotation_id}
**删除标注**

#### Query
| Name | Type | Description |
|------|------|-------------|
| annotation_id | string | 标注 ID |

---

### POST /apps/annotation-reply/{action}
**标注回复初始设置**

#### Query
| Name | Type | Description |
|------|------|-------------|
| action | string | 动作，只能是 'enable' 或 'disable' |
| embedding_provider_name | string | 指定的嵌入模型提供商 |
| embedding_model_name | string | 指定的嵌入模型 |
| score_threshold | number | 相似度阈值 |

---

### GET /apps/annotation-reply/{action}/status/{job_id}
**查询标注回复初始设置任务状态**

#### Query
| Name | Type | Description |
|------|------|-------------|
| action | string | 动作，必须和标注回复初始设置接口的动作一致 |
| job_id | string | 任务 ID |
