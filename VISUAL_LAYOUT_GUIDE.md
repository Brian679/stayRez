# Visual Layout Guide - StayRez Responsive Design

## Screen Layout Structure

### App Header (All Screens)
```
┌─────────────────────────────────────────────────┐
│  off Rez                              [← Back]  │  ← 10% height
└─────────────────────────────────────────────────┘
```

## Universities Page

### Mobile (< 577px) - 1 Column
```
┌─────────────────────────┐
│  off Rez      [← Back]  │
├─────────────────────────┤
│ Students Accommodation  │
│ Select a university...  │
├─────────────────────────┤
│ ┌─────────────────────┐ │
│ │  University Name 1  │ │
│ │  City Name          │ │
│ │  Admin Fee: $50     │ │
│ │  Description...     │ │
│ │  [View Properties]  │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │  University Name 2  │ │
│ │  ...                │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

### Tablet (577-768px) - 2 Columns
```
┌───────────────────────────────────────────┐
│  off Rez                        [← Back]  │
├───────────────────────────────────────────┤
│ Students Accommodation                    │
│ Select a university...                    │
├───────────────────────────────────────────┤
│ ┌──────────────┐  ┌──────────────┐       │
│ │ University 1 │  │ University 2 │       │
│ │ City Name    │  │ City Name    │       │
│ │ Admin: $50   │  │ Admin: $50   │       │
│ │ Description  │  │ Description  │       │
│ │ [View Props] │  │ [View Props] │       │
│ └──────────────┘  └──────────────┘       │
│ ┌──────────────┐  ┌──────────────┐       │
│ │ University 3 │  │ University 4 │       │
│ └──────────────┘  └──────────────┘       │
└───────────────────────────────────────────┘
```

### Desktop (769-992px) - 3 Columns
```
┌─────────────────────────────────────────────────────────┐
│  off Rez                                      [← Back]  │
├─────────────────────────────────────────────────────────┤
│ Students Accommodation                                  │
│ Select a university...                                  │
├─────────────────────────────────────────────────────────┤
│ ┌─────────┐  ┌─────────┐  ┌─────────┐                 │
│ │  Uni 1  │  │  Uni 2  │  │  Uni 3  │                 │
│ │  City   │  │  City   │  │  City   │                 │
│ │  $50    │  │  $50    │  │  $50    │                 │
│ │  Desc   │  │  Desc   │  │  Desc   │                 │
│ │ [View]  │  │ [View]  │  │ [View]  │                 │
│ └─────────┘  └─────────┘  └─────────┘                 │
└─────────────────────────────────────────────────────────┘
```

### Wide Screen (≥993px) - 4 Columns
```
┌───────────────────────────────────────────────────────────────────┐
│  off Rez                                            [← Back]      │
├───────────────────────────────────────────────────────────────────┤
│ Students Accommodation                                            │
│ Select a university...                                            │
├───────────────────────────────────────────────────────────────────┤
│ ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                          │
│ │ Uni1 │  │ Uni2 │  │ Uni3 │  │ Uni4 │                          │
│ │ City │  │ City │  │ City │  │ City │                          │
│ │ $50  │  │ $50  │  │ $50  │  │ $50  │                          │
│ │[View]│  │[View]│  │[View]│  │[View]│                          │
│ └──────┘  └──────┘  └──────┘  └──────┘                          │
└───────────────────────────────────────────────────────────────────┘
```

## Properties Page

### Mobile (< 577px) - 1 Column
```
┌──────────────────────────┐
│  off Rez   [← Univs]     │
├──────────────────────────┤
│ Properties for Uni Name  │
│ Filters: [Gender] [...]  │
├──────────────────────────┤
│ ┌──────────────────────┐ │
│ │  ┌──────────────┐   │ │
│ │  │    Image     │   │ │ ← 180px height
│ │  └──────────────┘   │ │
│ │  Property Title     │ │
│ │  Description...     │ │
│ │  Gender • Sharing   │ │
│ │  Price: $500        │ │
│ │  Distance: 2.5 km   │ │
│ │  [    View    ]     │ │ ← Full width button
│ └──────────────────────┘ │
│ ┌──────────────────────┐ │
│ │  Property 2...       │ │
│ └──────────────────────┘ │
└──────────────────────────┘
```

### Tablet (577-768px) - 2 Columns
```
┌────────────────────────────────────────────┐
│  off Rez                  [← Universities] │
├────────────────────────────────────────────┤
│ Properties for University Name             │
│ Filters: [Gender] [Sharing] [Price]        │
├────────────────────────────────────────────┤
│ ┌──────────────┐  ┌──────────────┐        │
│ │ ┌──────────┐ │  │ ┌──────────┐ │        │
│ │ │  Image   │ │  │ │  Image   │ │        │
│ │ └──────────┘ │  │ └──────────┘ │        │
│ │ Title        │  │ Title        │        │
│ │ Description  │  │ Description  │        │
│ │ Gender•Share │  │ Gender•Share │        │
│ │ Price: $500  │  │ Price: $600  │        │
│ │ [   View   ] │  │ [   View   ] │        │
│ └──────────────┘  └──────────────┘        │
└────────────────────────────────────────────┘
```

### Desktop (769-992px) - 3 Columns
```
┌──────────────────────────────────────────────────────────┐
│  off Rez                            [← Universities]     │
├──────────────────────────────────────────────────────────┤
│ Properties for University Name                           │
│ Filters: [Gender] [Sharing] [Price]                      │
├──────────────────────────────────────────────────────────┤
│ ┌─────────┐  ┌─────────┐  ┌─────────┐                  │
│ │ [Image] │  │ [Image] │  │ [Image] │                  │
│ │ Title 1 │  │ Title 2 │  │ Title 3 │                  │
│ │ Desc... │  │ Desc... │  │ Desc... │                  │
│ │ G•S     │  │ G•S     │  │ G•S     │                  │
│ │ $500    │  │ $600    │  │ $450    │                  │
│ │ [View]  │  │ [View]  │  │ [View]  │                  │
│ └─────────┘  └─────────┘  └─────────┘                  │
└──────────────────────────────────────────────────────────┘
```

### Wide Screen (≥993px) - 4 Columns
```
┌────────────────────────────────────────────────────────────────────┐
│  off Rez                                      [← Universities]     │
├────────────────────────────────────────────────────────────────────┤
│ Properties for University Name                                     │
│ Filters: [Gender] [Sharing] [Price] [Distance]                     │
├────────────────────────────────────────────────────────────────────┤
│ ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                           │
│ │[Img] │  │[Img] │  │[Img] │  │[Img] │                           │
│ │Title │  │Title │  │Title │  │Title │                           │
│ │Desc  │  │Desc  │  │Desc  │  │Desc  │                           │
│ │G•S   │  │G•S   │  │G•S   │  │G•S   │                           │
│ │$500  │  │$600  │  │$450  │  │$550  │                           │
│ │[View]│  │[View]│  │[View]│  │[View]│                           │
│ └──────┘  └──────┘  └──────┘  └──────┘                           │
└────────────────────────────────────────────────────────────────────┘
```

## Breakpoint Summary

| Screen Size | Width Range | Columns | Use Case |
|------------|-------------|---------|----------|
| Small      | < 577px     | 1       | Mobile phones (portrait) |
| Medium     | 577-768px   | 2       | Large phones (landscape), small tablets |
| Large      | 769-992px   | 3       | Tablets, small laptops |
| Extra Large| ≥ 993px     | 4       | Desktop monitors, large laptops |

## Card Dimensions

### University Cards
- Height: 180dp (mobile) / auto (web)
- Padding: 16px
- Border radius: 10px
- Gap: 20px

### Property Cards
- Height: 320dp (mobile) / auto (web)
- Image height: 180px/dp
- Padding: 16px
- Border radius: 10px
- Gap: 20px

## Color Reference

```
App Header Background: #fbf7f7ff
Card Background: #f7f7f7
"off" Text: #0f0e0eff (black)
"Rez" Text: #ffd700 (gold)
Primary Button: #0d6efd (blue)
Text Primary: #000000
Text Secondary: #6c757d
```
