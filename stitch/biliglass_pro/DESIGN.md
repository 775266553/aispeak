# 视觉语言规范：Bilibili 工具设计系统

这是一套专为 Bilibili 生态工具打造的高级、响应式设计系统。本系统的核心在于平衡“二次元”的活力与专业生产力工具的克制。我们不追求繁琐的装饰，而是通过光影、通透感和精准的排版来构建一个“高净值”的数字化工作空间。

---

## 1. 设计核心理念：灵动视窗 (The Ethereal Lens)

本系统的核心视觉北极星是**“灵动视窗”**。我们要打破传统 B 端工具沉闷的格子间布局，利用非对称的留白、重叠的半透明层级和极高对比度的标题字阶，营造一种“信息在呼吸”的感官体验。

- **打破平庸：** 严禁使用硬质线条分割区域。
- **动态深度：** 界面不再是扁平的纸张，而是由多层磨砂玻璃构成的立体空间。
- **意图导向：** 每一个圆角和阴影的参数调整，都是为了引导用户视觉流向最核心的内容。

---

## 2. 色彩系统 (Color Palette)

色彩不应只是填充，而是引导情绪的信号。我们基于 Bilibili 标志性的粉色进行深度的色调演化，确保在长久工作下视觉依然舒适。

### 核心调色板
- **Primary (品牌主色):** `#a42e56` (深粉) 到 `#fc739a` (柔粉) 的梯度应用。
- **Secondary (次要辅助):** `#006385` (深海蓝) 用于平衡粉色的跳跃感。
- **Tertiary (三级强调):** `#006479` (青翠色) 用于数据点缀或成功状态。
- **Background (底色):** `#f5f6f7` 确保在高光屏幕下不刺眼。

### 设计准则
- **“零线条”原则 (The No-Line Rule):** 严禁使用 1px 的实心边框（#CCCCCC 等）来划分版块。必须仅通过背景色阶的切换（如在 `surface` 背景上叠放 `surface-container-low` 区域）来定义边界。
- **层级嵌套 (Nesting Depth):** 模拟物理世界的堆叠。使用 `surface-container` 的五个能级（Lowest 至 Highest）进行嵌套。内层容器应比外层容器更亮（使用 `surface-container-lowest` 即纯白），从而产生自然向上的浮动感。
- **玻璃态与渐变:** 关键行动点（CTA）或悬浮面板必须结合 `backdrop-blur (20px-40px)` 与半透明的 `surface` 颜色。主按钮推荐使用从 `primary` 到 `primary_container` 的微弱纵向渐变，赋予其“果冻”般的质感。

---

## 3. 字体系统 (Typography)

针对简体中文（HarmonyOS Sans SC / Noto Sans SC）进行优化的排版系统，强调呼吸感与阅读节奏。

| 类型 | 字体 | 磅值 (Weight) | 情感引导 |
| :--- | :--- | :--- | :--- |
| **Display (大型显示)** | Plus Jakarta Sans / HarmonyOS | Bold (700) | 用于核心数据或欢迎语，展现科技感。 |
| **Headline (标题)** | HarmonyOS Sans SC | Medium (500) | 章节起始，界定清晰的阅读节奏。 |
| **Title (小标题)** | HarmonyOS Sans SC | Medium (500) | 卡片内信息的引导。 |
| **Body (正文)** | HarmonyOS Sans SC | Regular (400) | 确保在高密度文本下的极佳易读性。 |
| **Label (标签)** | HarmonyOS Sans SC | Regular (400) | 辅助信息，使用 `on-surface-variant` 色值。 |

**排版哲学：** 增加 `line-height` 至 1.6x 以上。标题应采用较大的字阶跳跃，创造“社论感”排版，而非传统的等距列表。

---

## 4. 提升与深度 (Elevation & Depth)

我们拒绝传统的投影，追求“环境光”效果。

- **色调层叠 (Tonal Layering):** 
  - 第一层：`background` (#f5f6f7) - 全局基底。
  - 第二层：`surface-container-low` - 侧边栏或次要容器。
  - 第三层：`surface-container-lowest` (#ffffff) - 核心内容卡片。
- **环境阴影 (Ambient Shadows):** 
  - 仅用于悬浮元素（如 Popover 或 Hover 态卡片）。
  - 参数：`X:0, Y:8, Blur:32, Spread:0`。
  - 颜色：必须带入品牌色相（如 `rgba(164, 46, 86, 0.06)`），而非纯黑色透明度。
- **幽灵边框 (Ghost Border):** 
  - 若必须强调边界，请使用 `outline-variant` 令牌并设定透明度为 15%。这能提供暗示性的边缘而不会割裂视觉。

---

## 5. 组件规范 (Components)

### 按钮 (Buttons)
- **Primary:** 使用 `primary` 填充，圆角设定为 `md (12px)`。文字使用 `on-primary`。
- **Secondary:** 仅使用 `surface-container-high` 填充，无边框，打造轻盈感。

### 卡片与列表 (Cards & Lists)
- **严禁分割线:** 列表项之间严禁出现水平分割线。请通过 `Spacing 3 (1rem)` 的垂直间距或在鼠标悬停时激活微弱的 `surface-container` 背景色来区分。
- **玻璃卡片:** 对重要的浮动面板使用 `background: rgba(255, 255, 255, 0.7)` 加 `backdrop-filter: blur(24px)`。

### 输入字段 (Input Fields)
- **静态:** 底色采用 `surface-container-lowest`，边框为 0。
- **聚焦:** 底部出现 2px 的 `primary` 呼吸条，而非全包围边框。

---

## 6. 红黑榜 (Do's and Don'ts)

### ✅ 推荐 (Do)
- 使用 `spacing-16` (5.5rem) 的超大页边距，让核心内容居中呼吸。
- 在页面顶部使用大面积的 `surface-bright` 与渐变背景的微弱交织。
- 所有的状态图标（如成功、警告）应使用圆润的填充风格，而非细线条。

### ❌ 避免 (Don't)
- **禁止使用纯黑 (#000000):** 请使用 `on-surface` (#2c2f30) 代替。
- **禁止锐利直角:** 除非是像素级装饰，否则所有容器圆角不得低于 `12px`。
- **禁止过度阴影:** 如果一个页面出现了超过 3 层阴影，请通过调整背景色阶重新简化层级。

---

## 7. 技术实现令牌 (Design Tokens Quick-Ref)

- **圆角 (Radius):** `lg: 16px`, `md: 12px`, `sm: 4px`
- **间距 (Spacing):** 
  - 标准模数：`1.4rem` (4) / `0.7rem` (2)
  - 核心呼吸感：`3.5rem` (10) 或 `5.5rem` (16)
- **透明度:** 
  - 玻璃态基础：`70%`
  - 幽灵边框：`15%`