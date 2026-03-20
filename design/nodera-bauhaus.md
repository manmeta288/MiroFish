// Nodera Bauhaus Design System
// This file contains all design tokens and rules for consistent page styling

export const NODERA_DESIGN_SYSTEM = {
  colors: {
    red: "#ff3b30",     // Primary actions, highlights, danger
    blue: "#017bfe",    // Primary brand, main elements, info
    yellow: "#ffcd00",  // Accents, secondary actions, warnings
    black: "#000000",   // Text, borders, strong elements
    white: "#ffffff"    // Backgrounds, contrast text
  },
  
  typography: {
    hero: "text-6xl font-bold tracking-tight",
    h1: "text-6xl font-bold tracking-tight",
    h2: "text-4xl font-bold",
    h3: "text-2xl font-bold",
    h4: "text-xl font-bold",
    body: "text-xl leading-relaxed",
    bodySmall: "text-lg leading-relaxed",
    small: "text-sm",
    caption: "text-xs"
  },
  
  spacing: {
    hero: "py-20",
    section: "py-20", 
    content: "py-20",
    between: "space-y-32",
    within: "space-y-8",
    small: "space-y-6",
    tiny: "space-y-4",
    container: "px-6"
  },
  
  shapes: {
    large: "w-64 h-64",
    medium: "w-48 h-48", 
    small: "w-32 h-32",
    accent: "w-24 h-24",
    tiny: "w-16 h-16",
    micro: "w-8 h-8"
  },
  
  layout: {
    hero: "relative overflow-hidden bg-white",
    container: "container mx-auto",
    content: "max-w-4xl mx-auto",
    grid: "grid md:grid-cols-2 gap-8",
    grid3: "grid md:grid-cols-3 gap-8"
  },
  
  borders: {
    thick: "border-8",
    medium: "border-4",
    thin: "border-2"
  },
  
  shadows: {
    bauhaus: "shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]",
    strong: "shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]",
    medium: "shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
  }
};

// Predefined hero shape configurations for different page types
export const HERO_SHAPES = {
  default: {
    left: { size: 'medium', type: 'square', color: 'yellow' },
    right: { size: 'accent', type: 'circle', color: 'red' },
    bottom: { size: 'small', type: 'circle', color: 'blue' }
  },
  
  networks: {
    left: { size: 'large', type: 'circle', color: 'red' },
    right: { size: 'small', type: 'square', color: 'yellow' },
    bottom: { size: 'medium', type: 'square', color: 'blue' }
  },
  
  operators: {
    left: { size: 'medium', type: 'square', color: 'blue' },
    right: { size: 'accent', type: 'circle', color: 'red' },
    bottom: { size: 'small', type: 'circle', color: 'yellow' }
  },
  
  community: {
    left: { size: 'small', type: 'square', color: 'yellow' },
    right: { size: 'accent', type: 'circle', color: 'red' },
    bottom: { size: 'medium', type: 'circle', color: 'blue' }
  },
  
  legal: {
    left: { size: 'accent', type: 'square', color: 'black' },
    right: { size: 'tiny', type: 'circle', color: 'blue' },
    bottom: { size: 'small', type: 'square', color: 'red' }
  },
  
  company: {
    left: { size: 'medium', type: 'circle', color: 'blue' },
    right: { size: 'small', type: 'square', color: 'yellow' },
    bottom: { size: 'accent', type: 'circle', color: 'red' }
  }
};

// Design system rules and guidelines
export const DESIGN_RULES = {
  // MUST FOLLOW rules
  layout: {
    hero: "Always use py-20 for hero sections",
    container: "Always use container mx-auto px-6",
    spacing: "Always use space-y-32 between sections",
    zIndex: "Always use z-10 for content above shapes"
  },
  
  colors: {
    primary: "Only use colors from NODERA_DESIGN_SYSTEM.colors",
    noCustom: "Never create custom colors in page components",
    contrast: "Always ensure sufficient contrast between text and background"
  },
  
  typography: {
    scale: "Only use typography tokens from the design system",
    hierarchy: "Maintain consistent heading hierarchy (h1 > h2 > h3 > h4)",
    noCustom: "Never override font sizes or weights"
  },
  
  shapes: {
    sizes: "Only use predefined shape sizes from the design system",
    positioning: "Use absolute positioning with specific coordinates",
    colors: "Shapes must use colors from the design system"
  },
  
  components: {
    structure: "Always use NoderaPageLayout for page structure",
    sections: "Use NoderaSection for content sections",
    features: "Use NoderaFeatureGrid for feature lists",
    infoBoxes: "Use NoderaInfoBox for highlighted content"
  }
};
