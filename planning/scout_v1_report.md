# Conference Format Scout Report

Scout version: v1 (2014 baseline)
Languages verified: English + Spanish (same format)
Conferences probed: 23 (2014/04 - 2025/04)

## Key Findings

1. **Single format breakpoint:** October 2024
   - 2014-2024/04: Sequential IDs (`p1`, `p2`, `author1`, `kicker1`)
   - 2024/10+: Hash IDs (`p_ks9eS`, `p_qFFZG`)

2. **URL pattern change:** 2019
   - 2014-2018: Title slugs (`/the-cost-and-blessings-of-discipleship`)
   - 2019+: Numbered (`/12andersen`)

3. **Spanish format:** Identical to English (same transition points)

4. **Footnotes structure:**
   - Markers: `<sup class="marker" data-value="1">`
   - Scripture refs: `<a class="scripture-ref" href="...">`
   - Footnotes JSON: `{note1: {id, marker, pid, text, referenceUris}}`

5. **100% probe success rate** - all conferences accessible via API

## Summary Table

| Year | Month | Talks | Para Format | Para Count | Has data-aid | Speaker Class | Status |
|------|-------|-------|-------------|------------|--------------|---------------|--------|
| 2014 | 04 | 46 | sequential | 53 | False | author-name | OK |
| 2014 | 10 | 45 | sequential | 34 | False | author-name | OK |
| 2015 | 04 | 45 | sequential | 44 | False | author-name | OK |
| 2015 | 10 | 46 | sequential | 37 | False | author-name | OK |
| 2016 | 04 | 44 | sequential | 42 | False | author-name | OK |
| 2016 | 10 | 44 | sequential | 63 | False | author-name | OK |
| 2017 | 04 | 45 | sequential | 54 | False | author-name | OK |
| 2017 | 10 | 42 | sequential | 39 | False | author-name | OK |
| 2018 | 04 | 43 | sequential | 55 | False | author-name | OK |
| 2018 | 10 | 39 | sequential | 59 | False | author-name | OK |
| 2019 | 04 | 38 | sequential | 30 | False | author-name | OK |
| 2019 | 10 | 40 | sequential | 47 | False | author-name | OK |
| 2020 | 04 | 40 | sequential | 77 | False | author-name | OK |
| 2020 | 10 | 41 | sequential | 67 | False | author-name | OK |
| 2021 | 04 | 42 | sequential | 97 | False | author-name | OK |
| 2021 | 10 | 45 | sequential | 43 | False | author-name | OK |
| 2022 | 04 | 43 | sequential | 32 | False | author-name | OK |
| 2022 | 10 | 41 | sequential | 83 | False | author-name | OK |
| 2023 | 04 | 40 | sequential | 39 | False | author-name | OK |
| 2023 | 10 | 38 | sequential | 85 | False | author-name | OK |
| 2024 | 04 | 39 | sequential | 10 | False | author-name | OK |
| 2024 | 10 | 40 | hash | 76 | False | author-name | OK |
| 2025 | 04 | 39 | hash | 10 | False | author-name | OK |

## Format Transitions

- **2024/10**: Changed from `sequential` to `hash`

## Sample Data

### 2014/04
- Talk: `/general-conference/2014/04/the-cost-and-blessings-of-discipleship`
- Paragraph IDs: `['p1', 'p2', 'kicker1', 'p3', 'p4']`
- Data-aids: `[]`
- Speaker: By Elder Jeffrey R. Holland

### 2014/10
- Talk: `/general-conference/2014/10/the-reason-for-our-hope`
- Paragraph IDs: `['p1', 'p2', 'kicker1', 'p3', 'p4']`
- Data-aids: `[]`
- Speaker: By President Boyd K. Packer

### 2015/04
- Talk: `/general-conference/2015/04/the-family-is-of-god`
- Paragraph IDs: `['p1', 'p2', 'kicker1', 'p3', 'p4']`
- Data-aids: `[]`
- Speaker: By Carole M. Stephens

### 2015/10
- Talk: `/general-conference/2015/10/worthy-of-our-promised-blessings`
- Paragraph IDs: `['p1', 'p2', 'kicker1', 'p3', 'p4']`
- Data-aids: `[]`
- Speaker: By Linda S. Reeves

### 2016/04
- Talk: `/general-conference/2016/04/what-shall-we-do`
- Paragraph IDs: `['p1', 'p2', 'kicker1', 'p3', 'p4']`
- Data-aids: `[]`
- Speaker: By Neill F. Marriott

### 2016/10
- Talk: `/general-conference/2016/10/the-master-healer`
- Paragraph IDs: `['p1', 'p2', 'kicker1', 'p3', 'p4']`
- Data-aids: `[]`
- Speaker: By Carole M. Stephens

### 2017/04
- Talk: `/general-conference/2017/04/the-beauty-of-holiness`
- Paragraph IDs: `['p1', 'p2', 'kicker1', 'p3', 'p4']`
- Data-aids: `[]`
- Speaker: By Carol F. McConkie

### 2017/10
- Talk: `/general-conference/2017/10/abiding-in-god-and-repairing-the-breach`
- Paragraph IDs: `['p1', 'p2', 'kicker1', 'p3', 'p4']`
- Data-aids: `[]`
- Speaker: By Neill F. Marriott

### 2018/04
- Talk: `/general-conference/2018/04/precious-gifts-from-god`
- Paragraph IDs: `['p1', 'p2', 'kicker1', 'p3', 'p4']`
- Data-aids: `[]`
- Speaker: By President M. Russell Ballard

### 2018/10
- Talk: `/general-conference/2018/10/deep-and-lasting-conversion-to-heavenly-father-and-the-lord-jesus-christ`
- Paragraph IDs: `['p1', 'p2', 'kicker1', 'p3', 'p4']`
- Data-aids: `[]`
- Speaker: By Elder Quentin L. Cook

### 2019/04
- Talk: `/general-conference/2019/04/12craven`
- Paragraph IDs: `['author1', 'author2', 'kicker1', 'p1', 'p2']`
- Data-aids: `[]`
- Speaker: By Becky Craven

### 2019/10
- Talk: `/general-conference/2019/10/12vinson`
- Paragraph IDs: `['author1', 'author2', 'kicker1', 'p1', 'p2']`
- Data-aids: `[]`
- Speaker: By Elder Terence M. Vinson

### 2020/04
- Talk: `/general-conference/2020/04/12ballard`
- Paragraph IDs: `['author1', 'author2', 'kicker1', 'p1', 'p2']`
- Data-aids: `[]`
- Speaker: By President M. Russell Ballard

### 2020/10
- Talk: `/general-conference/2020/10/12bednar`
- Paragraph IDs: `['subtitle1', 'author1', 'author2', 'kicker1', 'p1']`
- Data-aids: `[]`
- Speaker: By Elder David A. Bednar

### 2021/04
- Talk: `/general-conference/2021/04/12uchtdorf`
- Paragraph IDs: `['author1', 'author2', 'kicker1', 'p1', 'p2']`
- Data-aids: `[]`
- Speaker: By Elder Dieter F. Uchtdorf

### 2021/10
- Talk: `/general-conference/2021/10/12holland`
- Paragraph IDs: `['author1', 'author2', 'kicker1', 'p1', 'p2']`
- Data-aids: `[]`
- Speaker: By Elder Jeffrey R. Holland

### 2022/04
- Talk: `/general-conference/2022/04/12ballard`
- Paragraph IDs: `['author1', 'author2', 'kicker1', 'p1', 'p2']`
- Data-aids: `[]`
- Speaker: By President M. Russell Ballard

### 2022/10
- Talk: `/general-conference/2022/10/12uchtdorf`
- Paragraph IDs: `['author1', 'author2', 'kicker1', 'p1', 'p2']`
- Data-aids: `[]`
- Speaker: By Elder Dieter F. Uchtdorf

### 2023/04
- Talk: `/general-conference/2023/04/12cordon`
- Paragraph IDs: `['author1', 'author2', 'kicker1', 'p2', 'p3']`
- Data-aids: `[]`
- Speaker: By President Bonnie H. Cordon

### 2023/10
- Talk: `/general-conference/2023/10/12wright`
- Paragraph IDs: `['author1', 'author2', 'kicker1', 'p1', 'p2']`
- Data-aids: `[]`
- Speaker: By Sister Amy A. Wright

### 2024/04
- Talk: `/general-conference/2024/04/12larson`
- Paragraph IDs: `['author1', 'author2', 'p1', 'p2', 'p3']`
- Data-aids: `[]`
- Speaker: Presented by Jared B. Larson

### 2024/10
- Talk: `/general-conference/2024/10/12andersen`
- Paragraph IDs: `['p_ks9eS', 'p_qFFZG', 'p_ggZII', 'p_iJBUv', 'p_yV1hm']`
- Data-aids: `[]`
- Speaker: By Elder Neil L. Andersen

### 2025/04
- Talk: `/general-conference/2025/04/12larson`
- Paragraph IDs: `['p_ryPi0', 'p_f9OZT', 'p_aUtUc', 'p_oZdf0', 'p_dmhao']`
- Data-aids: `[]`
- Speaker: Presented by Jared B. Larson
