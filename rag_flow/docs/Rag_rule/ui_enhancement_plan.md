# 用户交互界面增强方案

## 1. 多端适配增强

### 1.1 移动端优化方案

#### 技术选型
- **跨平台框架**: Flutter + Dart
- **状态管理**: Provider + Riverpod
- **本地存储**: SQLite + Hive
- **离线支持**: 本地向量数据库 + 同步机制

#### 移动端架构设计

```dart
// 移动端核心服务架构
class MobileAppArchitecture {
  // 离线数据管理
  final OfflineDataManager offlineDataManager;
  
  // 语音输入服务
  final VoiceInputService voiceInputService;
  
  // OCR识别服务
  final OCRService ocrService;
  
  // 同步服务
  final SyncService syncService;
  
  // 诊断服务
  final DiagnosisService diagnosisService;
}

class OfflineDataManager {
  late Database _database;
  late Box _cacheBox;
  
  Future<void> initializeOfflineData() async {
    // 初始化本地数据库
    _database = await openDatabase('aviation_knowledge.db');
    
    // 初始化缓存
    _cacheBox = await Hive.openBox('knowledge_cache');
    
    // 下载核心知识库到本地
    await downloadCoreKnowledgeBase();
  }
  
  Future<List<SearchResult>> searchOffline(String query) async {
    // 本地向量检索实现
    final localResults = await _performLocalVectorSearch(query);
    return localResults;
  }
}
```

### 1.2 响应式Web界面

#### 技术选型
- **前端框架**: Vue 3 + TypeScript
- **UI组件库**: Element Plus + 自定义航空组件
- **状态管理**: Pinia
- **图表可视化**: D3.js + ECharts
- **实时通信**: WebSocket + Socket.io

#### 响应式设计方案

```typescript
// 响应式布局组件
interface ResponsiveLayoutProps {
  breakpoints: {
    mobile: number;
    tablet: number;
    desktop: number;
  };
}

class ResponsiveLayoutManager {
  private currentBreakpoint: string = 'desktop';
  
  constructor(private props: ResponsiveLayoutProps) {
    this.initializeResponsiveListeners();
  }
  
  private initializeResponsiveListeners(): void {
    window.addEventListener('resize', this.handleResize.bind(this));
    this.handleResize(); // 初始化
  }
  
  private handleResize(): void {
    const width = window.innerWidth;
    
    if (width <= this.props.breakpoints.mobile) {
      this.currentBreakpoint = 'mobile';
      this.applyMobileLayout();
    } else if (width <= this.props.breakpoints.tablet) {
      this.currentBreakpoint = 'tablet';
      this.applyTabletLayout();
    } else {
      this.currentBreakpoint = 'desktop';
      this.applyDesktopLayout();
    }
  }
  
  private applyMobileLayout(): void {
    // 移动端布局调整
    // - 单列布局
    // - 简化导航
    // - 大按钮设计
    // - 手势支持
  }
}
```

## 2. 语音输入与OCR识别

### 2.1 语音输入系统

#### 技术选型
- **语音识别**: 科大讯飞语音云 + 百度语音API
- **语音处理**: WebRTC + 噪声抑制
- **语音指令**: 自定义语音命令解析器
- **多语言支持**: 中英文混合识别

#### 语音输入实现

```python
class VoiceInputProcessor:
    """语音输入处理器"""
    
    def __init__(self):
        self.speech_recognizer = SpeechRecognizer()
        self.command_parser = VoiceCommandParser()
        self.noise_reducer = NoiseReducer()
        
    async def process_voice_input(self, audio_stream: bytes) -> VoiceInputResult:
        """
        处理语音输入
        
        Args:
            audio_stream: 音频流数据
            
        Returns:
            VoiceInputResult: 语音处理结果
        """
        # 1. 噪声抑制
        cleaned_audio = self.noise_reducer.reduce_noise(audio_stream)
        
        # 2. 语音识别
        recognition_result = await self.speech_recognizer.recognize(cleaned_audio)
        
        # 3. 命令解析
        if recognition_result.confidence > 0.8:
            parsed_command = self.command_parser.parse(recognition_result.text)
            
            if parsed_command.is_valid:
                return VoiceInputResult(
                    text=recognition_result.text,
                    command=parsed_command,
                    confidence=recognition_result.confidence,
                    status="success"
                )
        
        return VoiceInputResult(
            text=recognition_result.text,
            confidence=recognition_result.confidence,
            status="low_confidence"
        )

class VoiceCommandParser:
    """语音命令解析器"""
    
    def __init__(self):
        self.command_patterns = {
            'search': [
                r'搜索(.+)',
                r'查找(.+)',
                r'search for (.+)',
                r'find (.+)'
            ],
            'diagnose': [
                r'诊断(.+)故障',
                r'(.+)出现问题',
                r'diagnose (.+)',
                r'troubleshoot (.+)'
            ],
            'navigate': [
                r'打开(.+)',
                r'转到(.+)',
                r'open (.+)',
                r'go to (.+)'
            ]
        }
    
    def parse(self, text: str) -> VoiceCommand:
        """解析语音命令"""
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return VoiceCommand(
                        type=command_type,
                        parameters=match.groups(),
                        original_text=text,
                        is_valid=True
                    )
        
        return VoiceCommand(
            type="unknown",
            original_text=text,
            is_valid=False
        )
```

### 2.2 OCR识别系统

#### 技术选型
- **OCR引擎**: PaddleOCR + Tesseract
- **图像预处理**: OpenCV + PIL
- **文档结构识别**: LayoutLM + 自定义模型
- **表格识别**: TableNet + 后处理算法

#### OCR实现方案

```python
class OCRProcessor:
    """OCR识别处理器"""
    
    def __init__(self):
        self.ocr_engine = PaddleOCR(use_angle_cls=True, lang='ch')
        self.image_preprocessor = ImagePreprocessor()
        self.layout_analyzer = LayoutAnalyzer()
        self.table_recognizer = TableRecognizer()
    
    async def process_image(self, image_data: bytes) -> OCRResult:
        """
        处理图像OCR识别
        
        Args:
            image_data: 图像数据
            
        Returns:
            OCRResult: OCR识别结果
        """
        # 1. 图像预处理
        processed_image = self.image_preprocessor.preprocess(image_data)
        
        # 2. 布局分析
        layout_result = self.layout_analyzer.analyze(processed_image)
        
        # 3. 分区域OCR识别
        ocr_results = []
        for region in layout_result.regions:
            if region.type == 'text':
                text_result = await self._recognize_text_region(region.image)
                ocr_results.append(text_result)
            elif region.type == 'table':
                table_result = await self._recognize_table_region(region.image)
                ocr_results.append(table_result)
        
        # 4. 结果整合
        final_result = self._merge_ocr_results(ocr_results, layout_result)
        
        return final_result
    
    async def _recognize_text_region(self, region_image: np.ndarray) -> TextOCRResult:
        """识别文本区域"""
        result = self.ocr_engine.ocr(region_image, cls=True)
        
        text_blocks = []
        for line in result:
            for word_info in line:
                bbox, (text, confidence) = word_info
                text_blocks.append(TextBlock(
                    text=text,
                    bbox=bbox,
                    confidence=confidence
                ))
        
        return TextOCRResult(text_blocks=text_blocks)
    
    async def _recognize_table_region(self, region_image: np.ndarray) -> TableOCRResult:
        """识别表格区域"""
        # 表格结构识别
        table_structure = self.table_recognizer.recognize_structure(region_image)
        
        # 表格内容OCR
        table_content = []
        for cell in table_structure.cells:
            cell_image = self._extract_cell_image(region_image, cell.bbox)
            cell_text = self.ocr_engine.ocr(cell_image, cls=True)
            table_content.append(TableCell(
                row=cell.row,
                col=cell.col,
                text=cell_text,
                bbox=cell.bbox
            ))
        
        return TableOCRResult(
            structure=table_structure,
            content=table_content
        )

class ImagePreprocessor:
    """图像预处理器"""
    
    def preprocess(self, image_data: bytes) -> np.ndarray:
        """
        图像预处理
        
        Args:
            image_data: 原始图像数据
            
        Returns:
            np.ndarray: 预处理后的图像
        """
        # 1. 加载图像
        image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        
        # 2. 去噪
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        
        # 3. 倾斜校正
        corrected = self._correct_skew(denoised)
        
        # 4. 对比度增强
        enhanced = self._enhance_contrast(corrected)
        
        # 5. 二值化（如果需要）
        if self._should_binarize(enhanced):
            enhanced = self._adaptive_threshold(enhanced)
        
        return enhanced
    
    def _correct_skew(self, image: np.ndarray) -> np.ndarray:
        """倾斜校正"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            angles = []
            for rho, theta in lines[:, 0]:
                angle = theta * 180 / np.pi - 90
                angles.append(angle)
            
            # 计算平均角度
            median_angle = np.median(angles)
            
            # 旋转图像
            if abs(median_angle) > 0.5:  # 只有角度足够大才校正
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                return rotated
        
        return image
```

## 3. 可视化输出增强

### 3.1 流程图可视化

#### 技术选型
- **图形库**: D3.js + Cytoscape.js
- **流程图引擎**: 自定义流程图渲染器
- **导出功能**: Canvas2PDF + SVG导出
- **交互功能**: 缩放、拖拽、节点详情

#### 流程图实现

```typescript
class DiagnosisFlowchartRenderer {
    private container: HTMLElement;
    private cy: cytoscape.Core;
    
    constructor(containerId: string) {
        this.container = document.getElementById(containerId)!;
        this.initializeCytoscape();
    }
    
    private initializeCytoscape(): void {
        this.cy = cytoscape({
            container: this.container,
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': '#666',
                        'label': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '12px',
                        'width': '60px',
                        'height': '60px'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#ccc',
                        'target-arrow-color': '#ccc',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier'
                    }
                },
                {
                    selector: '.diagnosis-step',
                    style: {
                        'background-color': '#4CAF50',
                        'border-width': 2,
                        'border-color': '#2E7D32'
                    }
                },
                {
                    selector: '.fault-cause',
                    style: {
                        'background-color': '#F44336',
                        'border-width': 2,
                        'border-color': '#C62828'
                    }
                }
            ],
            layout: {
                name: 'dagre',
                rankDir: 'TB',
                spacingFactor: 1.5
            }
        });
    }
    
    public renderDiagnosisFlow(diagnosisResult: DiagnosisResult): void {
        const elements = this.buildFlowchartElements(diagnosisResult);
        
        this.cy.elements().remove();
        this.cy.add(elements);
        this.cy.layout({ name: 'dagre', rankDir: 'TB' }).run();
        
        // 添加交互事件
        this.addInteractionEvents();
    }
    
    private buildFlowchartElements(diagnosisResult: DiagnosisResult): any[] {
        const elements = [];
        
        // 添加症状节点
        diagnosisResult.symptoms.forEach((symptom, index) => {
            elements.push({
                data: {
                    id: `symptom-${index}`,
                    label: symptom.description,
                    type: 'symptom'
                },
                classes: 'symptom'
            });
        });
        
        // 添加诊断步骤节点
        diagnosisResult.diagnosisSteps.forEach((step, index) => {
            elements.push({
                data: {
                    id: `step-${index}`,
                    label: step.description,
                    type: 'diagnosis-step',
                    confidence: step.confidence
                },
                classes: 'diagnosis-step'
            });
        });
        
        // 添加可能原因节点
        diagnosisResult.possibleCauses.forEach((cause, index) => {
            elements.push({
                data: {
                    id: `cause-${index}`,
                    label: cause.description,
                    type: 'fault-cause',
                    probability: cause.probability
                },
                classes: 'fault-cause'
            });
        });
        
        // 添加连接边
        this.addConnectionEdges(elements, diagnosisResult);
        
        return elements;
    }
}
```

### 3.2 报告生成系统

```python
class ReportGenerator:
    """诊断报告生成器"""
    
    def __init__(self):
        self.template_engine = Jinja2Environment()
        self.pdf_generator = WeasyPrint()
        self.chart_generator = ChartGenerator()
    
    async def generate_diagnosis_report(self, diagnosis_result: DiagnosisResult, 
                                      format: str = 'pdf') -> ReportResult:
        """
        生成诊断报告
        
        Args:
            diagnosis_result: 诊断结果
            format: 报告格式 ('pdf', 'html', 'docx')
            
        Returns:
            ReportResult: 报告生成结果
        """
        # 1. 准备报告数据
        report_data = self._prepare_report_data(diagnosis_result)
        
        # 2. 生成图表
        charts = await self._generate_charts(diagnosis_result)
        report_data['charts'] = charts
        
        # 3. 渲染报告模板
        if format == 'pdf':
            report_content = await self._generate_pdf_report(report_data)
        elif format == 'html':
            report_content = await self._generate_html_report(report_data)
        elif format == 'docx':
            report_content = await self._generate_docx_report(report_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return ReportResult(
            content=report_content,
            format=format,
            filename=f"diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        )
    
    async def _generate_charts(self, diagnosis_result: DiagnosisResult) -> Dict[str, bytes]:
        """生成报告图表"""
        charts = {}
        
        # 1. 故障概率分布图
        probability_chart = self.chart_generator.create_probability_chart(
            diagnosis_result.possibleCauses
        )
        charts['probability_distribution'] = probability_chart
        
        # 2. 诊断流程图
        flowchart = self.chart_generator.create_diagnosis_flowchart(
            diagnosis_result.diagnosisSteps
        )
        charts['diagnosis_flowchart'] = flowchart
        
        # 3. 置信度趋势图
        confidence_chart = self.chart_generator.create_confidence_trend(
            diagnosis_result.confidenceHistory
        )
        charts['confidence_trend'] = confidence_chart
        
        return charts
```

## 4. 实施计划

### 4.1 开发阶段规划

**第一阶段（4周）：基础功能开发**
- 移动端基础框架搭建
- 语音输入基础功能
- OCR基础识别能力
- 响应式Web界面框架

**第二阶段（6周）：高级功能开发**
- 离线模式实现
- 高级语音命令解析
- 复杂文档OCR识别
- 流程图可视化

**第三阶段（4周）：集成优化**
- 多端数据同步
- 性能优化
- 用户体验优化
- 测试与调试

### 4.2 技术风险评估

**高风险项**：
- 移动端离线向量检索性能
- 语音识别在嘈杂环境下的准确率
- OCR对手写文档的识别效果

**应对策略**：
- 采用轻量级向量数据库（如Faiss）
- 多语音引擎融合提高准确率
- 结合人工校正机制提升OCR质量
