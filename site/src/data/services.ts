/* One source for the three services and the demo each one is proved by.
   The cards on the left and the cube's faces read from this, so the copy
   cannot drift between them. Opposite faces of the cube are a pair. */
export interface Pair {
  n: string;
  title: string;
  body: string;
  demo: string;
  demoName: string;
  /* Placeholder until the demo exists. Lives here rather than in tokens.css
     because colour belongs to the work, never to the container. */
  tint: string;
  onTint: string;
}

export const pairs: Pair[] = [
  {
    n: "01",
    title: "A brand's main site",
    body: "The one people land on when they look you up. Built once, properly, so it stops being the thing you apologize for.",
    demo: "Demo 01", demoName: "Helmet",
    tint: "#C4511F", onTint: "#FFFFFF",
  },
  {
    n: "02",
    title: "A launch site with a date on it",
    body: "One product, one moment, one page that has to be live before the drop. Everything on it points at the date.",
    demo: "Demo 02", demoName: "Fragrance",
    tint: "#E3D5BE", onTint: "#161614",
  },
  {
    n: "03",
    title: "A page that tells one story",
    body: "For the one thing that deserves more than a grid tile and three bullet points.",
    demo: "Demo 03", demoName: "Story",
    tint: "#A82A20", onTint: "#FFFFFF",
  },
];

/* Face order is front, back, right, left, top, bottom. Each service sits
   opposite the work that proves it, so either face opens the same panel. */
export const faces = [
  { fx: 0,   fy: 0,    svc: true,  i: 0 },
  { fx: 0,   fy: 180,  svc: false, i: 0 },
  { fx: 0,   fy: 90,   svc: true,  i: 1 },
  { fx: 0,   fy: -90,  svc: false, i: 1 },
  { fx: 90,  fy: 0,    svc: true,  i: 2 },
  { fx: -90, fy: 0,    svc: false, i: 2 },
];
