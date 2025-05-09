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

