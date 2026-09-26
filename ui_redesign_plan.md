# High-End Cinematic UI Redesign Plan

## Goal Description
The objective is to elevate the "Heritage Restore" frontend from a standard modern React app to an **award-winning, cinematic, Awwwards-level web experience**. The design will synthesize principles from art direction, motion design, scroll storytelling, and 3D web graphics (Three.js) to create an immersive environment that feels handcrafted and meticulously designed, aggressively avoiding any "AI-generated" or templated feel.

## Art Direction & Visual Language
- **Vibe:** Cinematic, Weightless, Impeccable, Historical yet Futuristic.
- **Color Palette:** Deep, rich darks (almost pitch black with slight warm undertones) contrasted with striking cinematic lighting (gold/amber volumetric glows).
- **Typography:** Extremely large, dramatic serif headers mixed with stark, highly legible sans-serif for utility text. Unconventional layouts (breaking the grid, offset typography).
- **Texture:** Very subtle film grain overlay across the entire experience to emphasize the "historical photograph" theme.

## Proposed Tech Stack Additions
- **Three.js & React Three Fiber (R3F):** For 3D WebGL background effects (e.g., floating golden particles, cinematic dust, or a 3D object transitioning from broken to restored).
- **Framer Motion & GSAP:** For advanced scroll-triggered animations, parallax storytelling, and fluid spring-based micro-interactions.
- **Lenis:** For buttery-smooth, hardware-accelerated smooth scrolling.
- **Shadcn/UI & Radix:** Unstyled, accessible primitives customized heavily to match the cinematic aesthetic.
- **Tailwind CSS v4:** Already installed, will be used for utility-first styling.

## Proposed Changes

---

### 1. Project Initialization & Dependencies
Install the required packages for high-end motion and 3D.
#### [NEW] Dependencies
- `three`, `@react-three/fiber`, `@react-three/drei` (WebGL / 3D)
- `framer-motion`, `gsap` (Animation & Scroll Storytelling)
- `@studio-freight/react-lenis` (Smooth Scrolling)
- `lucide-react` & `clsx`, `tailwind-merge` (Shadcn prerequisites)

---

### 2. Core Layout & Routing Structure
Wrap the application in a smooth scroll provider and a global grain overlay.
#### [MODIFY] `src/App.jsx`
- Wrap routes in `<ReactLenis root>`.
- Add a global `<FilmGrain />` component fixed to the viewport.
- Wrap page transitions in `AnimatePresence`.

#### [MODIFY] `src/index.css`
- Add custom CSS animations for the noise overlay.
- Define selection colors and custom scrollbar hiding.

---

### 3. The Cinematic Home Page (Scroll Storytelling)
Redesign `Home.jsx` into a continuous, narrative-driven scroll experience.
#### [MODIFY] `src/pages/Home.jsx`
- **Hero Section:** Full-viewport height. A massive, dramatic typographic header. In the background, a React Three Fiber canvas rendering floating 3D dust particles reacting to cursor movement (parallax).
- **Story Section:** As the user scrolls, text reveals line-by-line (GSAP ScrollTrigger or Framer Motion `useScroll`), telling the story of preserving history.
- **Bento Grid / Action Section:** The "Restore" and "Identify" entry points presented as highly polished, interactive 3D-like cards that tilt on mouse move (`@react-three/drei` or Framer Motion 3D transforms).

---

### 4. Restoration Experience (Impeccable UI)
Transform the tool into a professional, dark-room-like workspace.
#### [MODIFY] `src/pages/RestorePage.jsx`
- **Upload Zone:** Replace the standard dashed border with a cinematic glowing ring or magnetic drop zone that reacts to drag events with spring physics.
- **Processing State:** Instead of a standard progress bar, use a high-end cinematic loader (e.g., scanning line over the image, glowing particle emission).
- **Comparison:** Enhance `BeforeAfterSlider.jsx` with a custom SVG handle and fluid dragging physics.

---

### 5. Identification Experience (Data & UI)
#### [MODIFY] `src/pages/IdentifyPage.jsx` & `HistoryDetail.jsx`
- Render the monument history as a highly curated editorial piece (like a NYT Interactive).
- Large images, offset text, dramatic drop caps.
- Timeline rendered with smooth SVG line drawing animations on scroll.

---

## User Review Required
> [!IMPORTANT]  
> **Performance vs. Aesthetics:** Adding Three.js and continuous smooth scrolling will increase bundle size and GPU usage. Is the priority strictly on a jaw-dropping visual experience (award-winning) even if it requires modern hardware to run smoothly?

> [!WARNING]  
> **3D Assets:** Do you have a specific 3D model (e.g., a bust or monument) you'd like to feature in the WebGL hero canvas? If not, I will create a procedural particle/dust system that fits the historical vibe without requiring external asset loading.

## Verification Plan
### Automated Tests
- Run `npm run build` to ensure the new 3D and animation dependencies bundle successfully without Vite errors.
### Manual Verification
- Verify that scrolling feels smooth (Lenis).
- Verify the WebGL canvas renders without dropping framerates.
- Ensure the UI feels distinctly cinematic, with no generic centered-card "slop".

---
*Awaiting your approval to begin execution.*
