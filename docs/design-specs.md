# Design Specifications - Modern Teal Light Theme

## 🎨 Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| **Primary** | `#0D9488` | Main buttons, active states, key accents (Teal-600) |
| Primary Light | `#2DD4BF` | Hover states, subtle highlights (Teal-400) |
| Primary Dark | `#0F766E` | Pressed states, heavy borders (Teal-700) |
| **Background** | `#F8FAFC` | Main application background (Slate-50) |
| Surface | `#FFFFFF` | Cards, input fields, sidebar (White) |
| Surface Alt | `#F1F5F9` | Secondary backgrounds, hover areas (Slate-100) |
| **Text Primary** | `#0F172A` | Headings, main text (Slate-900) |
| Text Secondary | `#64748B` | Subtitles, placeholders (Slate-500) |
| Border | `#E2E8F0` | Dividers, input borders (Slate-200) |
| Border Focus | `#0D9488` | Active input borders |
| Error | `#EF4444` | Error messages (Red-500) |
| Success | `#10B981` | Success states (Emerald-500) |

## 📐 Shape & Geometry

* **Style**: Sharp / Professional (Windows 11 inspired).
* **Border Radius**:
  * `sm` (4px): Checkboxes, tags.
  * `md` (6px): Buttons, Input fields, Cards.
  * `lg` (8px): Modals, Dialogs.

## ✒️ Typography

* **Font**: Segoe UI (Windows default) or Inter.
* **Sizes**:
  * Headings: 24px (Bold)
  * Subheadings: 18px (SemiBold)
  * Body: 14px (Regular)
  * Small: 12px (Regular)

## 🎇 Effects

* **Shadows**: Subtle, diffuse shadows for depth (only on cards/modals).
  * Card: `0 2px 4px rgba(0,0,0,0.05)`
* **Gradients**: Very subtle linear gradient for the Login Background (Teal-50 to White).

## 🧩 Component Behaviors

* **Buttons**: Flat design, slightly rounded. Hover lifts brightness.
* **Inputs**: White background, gray border. Focus changes border to Primary Teal.
* **Sidebar**: White or very light gray (`#F8FAFC`). Active item has Teal text and subtle Teal background tint.
