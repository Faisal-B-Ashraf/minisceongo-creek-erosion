# Minisceongo Creek "M" bend: south bank erosion study

This is the knowledge base for the project assistant. It explains, in plain English, everything that was done in the study:
the question, the data, each step of the method (the same 10 steps as the animation), the numbers, the checks, the results,
the assumptions and the limits. Distances are in feet (ft). Coordinates are NAD83 New York State Plane East, US survey feet
(EPSG 2260). Elevations are NAVD88, in feet.

## Project summary
<!-- steps: 0,9 -->

### The short answer
<!-- steps: 0,9 -->
Between 19 November 2011 and 15 April 2022 (10.4 years), the south bank of the "M"-shaped bend of Minisceongo Creek behind
Samsondale Avenue stayed put along almost its whole length: the creek-facing south bank moved less than about 1.5 ft, which is
within the measurement error. There is one active erosion spot: stations 72 to 75, where the creek leaves the dip (the outside
of the bend). There the south bank moved toward the houses by 2.6 ft (station 72), 6.2 ft (73), 9.1 ft (74) and 1.5 ft (75).
The worst point, station 74, averages about 0.9 ft per year. Station 66 moved 2.0 ft. Stations 36 and 100 moved about
1.5 to 1.7 ft, just over the error limit (borderline). The bank moved toward the creek (build-up) by 1.4 to 3.0 ft at stations
38, 77, 79 and 80.

### Where the study is
<!-- steps: 0,1 -->
The study covers the "M"-shaped bend of Minisceongo Creek behind Samsondale Avenue in West Haverstraw (Town of Haverstraw),
Rockland County, New York. In this reach the creek flows roughly from west to east. The bend has two humps (outside bends that
bulge to the north) with a dip between them. Houses, a cul-de-sac and yards sit on the south side of the creek; Samsondale
Avenue runs along the north-east corner. The study box is E 635,900 to 636,850 and N 863,650 to 864,150 (950 ft by 500 ft).

### What question the study answers
<!-- steps: 0 -->
The question is: has the creek's SOUTH bank (the house side) moved toward the houses, where, by how much and how fast? The
south bank is the bank on your right when you look downstream. Only the south bank matters here because that is the side with
the homes, yards and the embankment along Samsondale Avenue. The north bank is mostly wooded land.

### What data was used
<!-- steps: 0,1,5 -->
Two kinds of free public data were used:
- Aerial photos (orthophotos) from the New York State Statewide Digital Orthoimagery Program for 2004, 2007, 2010, 2013, 2016,
  2021, 2024 and 2025, mostly flown in spring with the leaves off. They were used to draw the creek centreline and for visual
  checks.
- Two airborne lidar (laser) surveys: USGS, flown 19 November 2011, and New York State, flown 15 April 2022. They were used for
  all bank measurements.
One 2026 commercial aerial photo (0.25-ft pixels, licensed) was also used, only to help draw the centreline. It is not included
in this repository. Every number about bank movement comes from the two lidar surveys, not from the photos.

### Who did the work and when
<!-- steps: 0 -->
The study was carried out in September 2026 by Faisal Ashraf (GitHub: Faisal-B-Ashraf) as a desktop study using public data.
It is not a substitute for a field inspection or a stamped engineering report.

## The method in 10 steps
<!-- steps: 0 -->

### Overview of the 10 steps
<!-- steps: 0 -->
1. The question: is the south bank moving toward the houses?
2. Line up the photos so every year sits exactly on top of the others.
3. Score every pixel for how red-brown it is and average the years, so the creek shows up as one dark band.
4. Draw a creek centreline with a "cheapest path" computer search along the dark band.
5. Put a station every 10 ft along the centreline and draw a cross line square to the creek at each station.
6. Take the two lidar surveys (2011 and 2022), keep only ground points, and line the 2011 survey up with the 2022 survey.
7. Turn each survey's ground points into its own ground surface (a DEM) on a 1-ft grid.
8. Cut both surfaces along each cross line (a cross-section) and measure how far the south bank moved.
9. Repeat at all 128 stations and keep only changes bigger than the measurement error.
10. Read the answer: one active erosion spot at stations 72 to 75.
The photos (steps 2 to 5) only build the ruler (the centreline and stations). The measurement itself (steps 6 to 9) uses lidar.

## Step 1: the question
<!-- steps: 0 -->

### What the first scene shows
<!-- steps: 0 -->
The first scene shows the bend on the 2025 state aerial photo. The yellow line is the south bank (house side) as measured from
the 2022 lidar, drawn where the bank faces the creek. The blue arrow shows the flow direction (west to east). The north bank is
at the top of the picture, the houses and the cul-de-sac at the bottom.

### Why only the south bank
<!-- steps: 0 -->
The south bank is where the homes, yards and the Samsondale Avenue embankment are, so a bank moving that way is what could
threaten property and infrastructure. The north bank was looked at only when it helped explain the south bank (for example the
north bank of the dip is eroding as the channel shifts north).

## Step 2: lining up the photos
<!-- steps: 1 -->

### Why the photos had to be lined up
<!-- steps: 1 -->
Photos from different years do not sit exactly on top of each other. Each flight has small position errors, so the same curb
can be 1 to 2.5 ft apart between years (2004 is much worse). Before combining the photos, every photo was slid so that it sits
on the 2025 photo. Note: the photos only build the measuring ruler (the centreline). A small photo error cannot create or hide
bank movement, because the bank is measured on lidar, and both lidar years are measured on the same ruler.

### Which landmarks were used and why
<!-- steps: 1 -->
Only things that do not move were used: curbs, driveways, road edges, house roofs and Samsondale Avenue. They sit in two areas:
the strip of houses and streets along the south of the study box (N 863,650 to 863,830) and Samsondale Avenue in the north-east
corner. Trees, grass, shadows and the creek itself were NOT used because they change from year to year (leaves, sun angle,
water level, and the erosion we are trying to measure).

### What the 40-ft squares (rectangles) are and why that size
<!-- steps: 1 -->
The squares are small windows, 40 ft by 40 ft (80 by 80 pixels at 0.5 ft), placed every 25 ft over the landmark areas. Each
square holds one local pattern, for example a curve of curb or a roof corner. A square is used instead of the whole photo so
that each match looks at one clear landmark; 40 ft is big enough to hold a recognisable pattern and small enough to stay local.
For 2016, 204 squares were tried and 45 found a clear match. Squares over trees, shadows or plain grass had no clear pattern
and were skipped.

### What the fit score measures
<!-- steps: 1 -->
For each square, the computer cuts it out of the 2025 photo and slides it over the other photo, up to 15 ft in every direction,
in half-foot steps. At each position it computes a fit score called normalised cross-correlation: it compares the pattern of
light and dark in the square with the photo underneath. 1 means a perfect match, 0 means no relationship. Before matching, both
photos are edge-enhanced (a difference-of-Gaussians filter keeps outlines about 1 to 6 ft wide and removes overall brightness and
colour differences between flights). A square counts only if its best score is at least 0.35 and the best spot is not on the
edge of the search area. The best spot is refined to a fraction of a pixel. Where the best spot sits tells how far that photo
is off at that square.

### Why the middle value (median) is used
<!-- steps: 1 -->
Each good square gives its own answer (how far the photo is off, east and north). Most agree within 1 to 2 ft, but a few are
fooled (a parked car that moved, a new shed). The middle value (median) of all squares ignores those few bad ones. For 2016 the
middle value was 0.4 ft east and 1.0 ft south: the 2016 photo sat that far from the 2025 photo, and the whole 2016 photo was
slid back by that amount. Nothing is stretched or rotated; the photo is only slid.

### How far each photo was off
<!-- steps: 1 -->
Offsets of each photo compared with NYS 2025 (east, north; + = east / north):
- 2004: 0.0 ft E, 4.0 ft S, but the squares disagreed by 7 to 9 ft, so 2004 was used for pictures only.
- 2007: 1.2 ft W, 0.0 ft N.
- 2010: 1.5 ft W, 0.5 ft S.
- 2013: 1.3 ft W, 1.0 ft S.
- 2016: 0.4 ft E, 1.0 ft S.
- 2021: 0.1 ft E, 1.8 ft S.
- 2024: 0.0 ft E, 0.6 ft S.
- 2026 commercial photo: 0.4 ft W, 2.4 ft N.
The typical scatter between squares was about 1 to 2 ft. The 1994 photo (1-metre pixels) could not be matched and was not used.

### Different photo resolutions
<!-- steps: 1 -->
All photos were first put on the same grid: the same 950 x 500 ft box with 0.5-ft pixels (1,900 x 1,000 pixels). The state
photos are delivered at 0.5 ft, but a sharpness check shows their real detail is about 0.75 to 0.9 ft; 2004 is about 1 ft; the
commercial 2026 photo is truly sharper (0.25 ft source). A blurrier photo shows the same curb in the same place, only softer.
The matching compares outlines 1 to 6 ft wide, which all the photos show, so the resolution difference does not bias the result.

## Step 3: the score and the averaged photo
<!-- steps: 2 -->

### How each pixel is scored
<!-- steps: 2 -->
In spring photos, with the leaves off, soil and dead leaves are red-brown, while water, shadows and grey roofs are not. Each
pixel gets a redness value: (red minus blue) divided by (red + green + blue). The value is smoothed over about 1 ft and then
turned into a score within that photo: the score is (redness minus the photo's median redness) divided by the spread of the
middle half of the photo's pixels (the interquartile range). So 0 means "a typical pixel of that photo", minus means less red
(water-like, dark on the grey pictures) and plus means more red (soil and leaves, light). Scoring within each photo cancels the
differences in brightness and colour between flights.

### Example scores
<!-- steps: 2 -->
In the 2016 photo, a creek pixel with red 22, green 37 and blue 61 has a redness of -0.325 and a score of about -4.7 (very
water-like). A ground pixel with red 122, green 110 and blue 110 has a redness of +0.035 and a score of about +0.3 (typical).
For the whole 2016 photo the median redness was +0.015 and the middle half ran from -0.029 to +0.048.

### Why several years are averaged
<!-- steps: 2 -->
In any one photo, shadows, sun glare and dark roofs also look "not red". Averaging the scores of many years, pixel by pixel,
makes things that appear in only one year fade away, while the creek is dark in every year and becomes one clean dark band.
The animation shows the average of the seven state photos from 2007 to 2025. The centreline actually used in the analysis was
drawn on the average of eight photos: those seven plus the 2026 commercial photo; the difference is too small to see. Each photo
was first slid by its offset from step 2. The 2004 photo was left out because it lined up poorly, and 1994 could not be lined up.

### Why redness and not just darkness
<!-- steps: 2 -->
Plain darkness changes a lot between flights (time of day, haze, camera). Redness compared within each photo is much more
stable: leaf-off ground is always red-brown, water and deep shadow are not. Infrared (colour-infrared) versions of the photos
exist for most years and were used in an early test, but the final centreline uses redness from the natural-colour photos.

## Step 4: drawing the centreline
<!-- steps: 3 -->

### What the centreline is for
<!-- steps: 3 -->
The centreline is a fixed ruler down the middle of the creek, drawn once and used for every year. It gives the stations and the
cross lines, so that 2011 and 2022 are measured at exactly the same places. It is not the deepest point of the channel (the
thalweg) and it does not move between years. Bank movement is measured as the change in distance from this same line, so its
exact position does not change the result.

### How the cheapest path works
<!-- steps: 3 -->
The averaged score picture is resampled to a 1-ft grid (950 x 500 cells). Every 1-ft step between neighbouring cells has a price:
e to the power (1.5 x score), with the score clipped to -3 to +3. A very water-like cell (score -3) costs about 0.01, a typical
cell costs 1 and a very red cell (score +3) costs about 90. Diagonal steps cost 1.41 times more because they are longer. The
computer (Dijkstra's shortest-path algorithm, from the SciPy library) finds the route from START to END with the lowest total
price. START is the least-red point on the west edge of the box and END is the least-red point on the east edge, which is where
the creek enters and leaves.

### Why the line does not go through dark roofs or shadows
<!-- steps: 3 -->
Roofs, the cul-de-sac and shadows are also dark (cheap), but they are isolated. To use them, the route would have to cross
expensive red ground to get there and cross it again to get back to the END. In the animation, the "water poured at START"
spreads into those dark spots but they lead nowhere. A test route forced through the darkest roof costs 2.3 times more than the
route along the creek, so the cheapest route follows the creek.

### Smoothing and length
<!-- steps: 3 -->
The raw route follows every small wiggle of the dark band, so it is smoothed with a 20-ft moving average. Points are then placed
every 10 ft along it. The final centreline is 1,270 ft long.

## Step 5: stations and cross lines
<!-- steps: 4 -->

### What stations are
<!-- steps: 4 -->
A station is a point on the centreline every 10 ft, numbered 0 at the west (upstream) end to 127 at the east (downstream) end.
Station 74 is 740 ft along the creek. There are 128 stations in total.

### What cross lines are and how long they are
<!-- steps: 4 -->
At each station a cross line is drawn square (perpendicular) to the centreline, using the local direction of the line. In the
animation the lines run 30 ft to the north and 45 ft to the south. For the lidar measurement the cross-sections are longer, 40 ft
to the north and 80 ft to the south, so they reach the top of the high banks. Both survey years are always cut on the same
lines.

### Why every 10 ft
<!-- steps: 4 -->
10 ft is close enough to catch a local bank failure (the active spot at stations 72 to 75 covers about 40 ft) and far enough
apart that neighbouring measurements are nearly independent. It gives 128 measurements along the 1,270-ft bend.

### The five sections of the M
<!-- steps: 4,8 -->
For reporting, the stations are grouped into five sections:
- West limb: stations 0 to 35.
- First hump (the inside of the first bend, seen from the south): stations 36 to 57.
- Dip (the outside of the bend, nearest the houses): stations 58 to 75.
- Pool and second hump: stations 76 to 99.
- East limb: stations 100 to 127.

## Step 6: the two lidar surveys
<!-- steps: 5 -->

### What lidar is
<!-- steps: 5 -->
Lidar is a laser scanner flown in a plane. It fires hundreds of thousands of laser pulses per second, and every return becomes a
point with an exact position (east, north) and height. In leaf-off season many pulses reach the ground between the branches. The
survey company labels every point: ground, low or high vegetation, building, water, noise, and so on.

### The 2011 survey
<!-- steps: 5 -->
The first survey is part of the USGS Northeast lidar project (ARRA_LFTNE_NEWYORK_2010). The project was flown between December
2010 and December 2011; the tile covering this site (18_05854562) was flown on 19 November 2011, read from the time stamps in the
file. It was delivered in UTM zone 18N metres (NAD83) with NAVD88 heights (Geoid09). In the study box it has 28,619 ground points,
about one every 4 ft. The ground points used are classes 2 (ground) and 18. Class 18 is a non-standard class in this delivery
(overlap ground); it was checked first: 84 percent of its points lie within 0.5 ft of the class-2 ground.

### The 2022 survey
<!-- steps: 5 -->
The second survey is the New York State "Southeast 4 County 2022" lidar project, flown 9 to 30 April 2022; the tile covering this
site (u_5850056150) was flown on 15 April 2022. It was delivered in UTM zone 18N metres (NAD83 2011) with NAVD88 heights
(Geoid18). In the study box it has 120,068 ground points, about one every 2 ft. Class 2 (ground) is used. Both tiles were
downloaded from the NYS GIS Clearinghouse (gisdata.ny.gov) and converted to NY State Plane East feet and to elevations in feet.

### Why only two lidar surveys
<!-- steps: 5 -->
Only two lidar surveys cover this spot: 2011 and 2022 (checked in the state and USGS lidar indexes). Two surveys give one
before-and-after comparison, not a trend, so the result is an average over 10.4 years. The aerial photos cover more years but
cannot measure a bank under trees and shadows accurately.

### Why the 2011 survey had to be moved 6.7 ft
<!-- steps: 5 -->
When the two surveys are laid on top of each other as delivered, the same houses do not line up: the 2011 survey sits about
6.7 ft north-west of the 2022 survey. Older surveys often have this kind of offset. On a steep bank, a 6.7-ft sideways offset
would look like several feet of false bank movement, so it had to be removed before measuring anything.

### How the two surveys were lined up (house roofs)
<!-- steps: 5 -->
For each survey, a "height above the ground nearby" map was made on a 1-ft grid, using all points except noise. On these maps a
house is a flat block 15 to 30 ft high. The 2011 map was cut into 60-ft windows that contain roofs and each window was slid over
the 2022 map (up to 12 ft each way) until the roofs overlapped best (match score at least 0.7). 29 windows gave a clear answer.
Single houses differ by about 2 ft (for example one house said 0.4 ft east and 7.5 ft south), so the middle value was used: move
2011 by 2.6 ft east and 6.1 ft south. Roofs are good landmarks because they are sharp, tall and do not move. A sparser survey
does not move a roof; it only gives fewer points along its edges.

### Fine-tuning on hillsides and the final shift
<!-- steps: 5 -->
The shift was then fine-tuned on hillsides more than 70 ft from the creek (ground that should not have changed), using the
Nuth and Kaab slope-and-aspect method. The final move for every 2011 point is 2.2 ft east and 6.4 ft south (2.21 E, 6.37 S),
about 6.7 ft in total. Nothing is stretched or rotated: every point gets the same two numbers added to its coordinates, like
sliding tracing paper.

### The hillside check: what the wave means
<!-- steps: 5 -->
If one survey sits sideways, a hill shows fake height changes: the slope facing one way looks lower, the slope facing the other
way looks higher, and flat ground shows nothing. Sorting about 145,000 hillside cells by the direction they face and plotting
height change divided by steepness gives a wave. The size of the wave is the sideways mismatch that is left. As delivered the
wave was 2.9 ft (this test under-reads large shifts, which is why the roofs did the big move), after the roof shift 0.5 ft, and
after fine-tuning only 0.2 ft. So "hillsides matched within 0.2 ft" means the leftover sideways error after alignment is 0.2 ft.

### Tying the lidar to the photos and removing the height bias
<!-- steps: 5 -->
The 2022 lidar was compared with the 2025 infrared photo by matching the lidar's laser brightness (intensity) to the photo. It
sat 0.25 ft east and 1.74 ft north of the photos, so both lidar years were moved by that same small amount to sit on the photo
map; this only places the stations and cannot create movement, because both years get the same move. Finally, on flat ground
away from the creek (yards and roads) the 2022 heights were 0.08 ft lower on average than 2011, and that small bias was removed.
Total moves applied: 2011 points 1.96 ft east and 8.11 ft south; 2022 points 0.25 ft west and 1.74 ft south.

## Step 7: ground surfaces (DEMs)
<!-- steps: 6 -->

### How the ground points become a surface
<!-- steps: 6 -->
The ground points of each survey are joined into small triangles (a Delaunay triangulation, or TIN), like a net thrown over the
ground, and the height is read off the triangles every 1 ft. The result is a digital elevation model (DEM) for each survey:
Ground_DEM_2011_Nov_1ft and Ground_DEM_2022_Apr_1ft. Where there is no ground point within 10 ft (2011) or 6 ft (2022), for
example under houses or over open water, the surface is left blank.

### Why the two surveys are never merged
<!-- steps: 6 -->
The point of the study is to compare two dates, so each survey keeps its own surface. They are only compared, cross line by cross
line, and in an elevation-change map (2022 minus 2011).

### Why there is no data under the water
<!-- steps: 6 -->
The lidar used here is a normal (near-infrared) laser, which is absorbed by water, so it cannot see the creek bed. Over the
channel there are either no ground points or a few points on the water surface. That is why only the dry bank face is measured,
from its toe upward, and why the channel bottom is not part of the result. The water level was also different on the two flight
days (November 2011 and April 2022).

### How much noise there is on stable ground
<!-- steps: 6 -->
Comparing the two surfaces on ground that should not change (more than 70 ft from the creek) shows the height noise (NMAD, a
robust standard deviation): 0.20 ft on flat ground (0 to 5 degrees), 0.26 ft on gentle slopes (5 to 15 degrees), 0.41 ft on steep
slopes (15 to 30 degrees) and 0.59 ft on very steep slopes (30 to 60 degrees). Height changes smaller than about twice these
values (0.4 to 1.2 ft) are hidden on the change map.

## Step 8: one cross-section and how the bank is measured
<!-- steps: 7 -->

### What a cross-section is
<!-- steps: 7 -->
A cross-section is the shape of the ground along one cross line: distance from the centreline on the horizontal axis (minus =
north, plus = south, toward the houses) and ground elevation on the vertical axis. Both surfaces are read every 0.5 ft along the
same line, giving a 2011 profile (blue) and a 2022 profile (red). Where the red bank face sits to the right of the blue one, the
bank moved toward the houses.

### How the bank face is found
<!-- steps: 7 -->
On the 2022 profile, south of the water's edge, the computer looks for stretches steeper than about 8.5 degrees (slope 0.15),
joining stretches separated by less than 3 ft. The bank face is the tallest of those stretches (so a low gravel-bar edge in front
of the real bank is not mistaken for it). It must be at least 2 ft high. Where the face runs straight up into the valley wall,
only its lowest 12 ft are used, because that is the part the creek attacks.

### Why the bank is measured at three heights
<!-- steps: 7 -->
The bank position is measured at 25, 50 and 75 percent of the face height (from its toe). At each height the computer finds where
each year's profile crosses that elevation, within 20 ft of the face, and reads its distance from the centreline. Using three
heights instead of one edge makes the result less sensitive to a single bump or a missing point, and shows whether the whole face
moved or only its foot. Movement = 2022 distance minus 2011 distance, averaged over the three heights. Plus means the bank moved
toward the houses (erosion); minus means it built up toward the creek.

### Station 74 in numbers
<!-- steps: 7,9 -->
Station 74 (740 ft along the creek) is where the creek leaves the dip. The 2022 bank face runs from a toe at about 20.6 ft
elevation up past 34 ft, at about 65 degrees; the lowest 12 ft were measured, at heights of about 23.6, 26.6 and 29.6 ft. The bank
moved toward the houses by +10.3 ft at the lowest height, +9.3 ft in the middle and +7.7 ft at the top: an average of +9.1 ft.
At mid-height the bank was 20.3 ft from the centreline in 2011 and 29.6 ft in 2022. The error limit at this station is 1.3 ft, so
the change is real. Over 10.4 years that is about 0.9 ft per year on average. The foot moved more than the top, which fits a bank
being undercut and then slumping.

### What "set back" means
<!-- steps: 7,8 -->
Some high banks stand back from the water behind a raised gravel bar or bench. A bank is called "set back" when its toe is more
than 15 ft behind the water's edge AND the ground in front of it is more than 1.5 ft above the channel bottom. The creek does not
touch those banks at normal flows, so changes there (such as yard work or fill) are reported but not counted as creek erosion.
In the charts they are drawn as pale or hatched bars.

### The error limit (detection limit)
<!-- steps: 7,8 -->
A movement counts as real only if it is bigger than the 95 percent detection limit of that station, which combines three
measured errors:
- Few points in 2011: the 2022 points were thinned at random to the 2011 density (about a quarter of the points) ten times and the
  bank was measured again each time. The sparse sampling adds about plus or minus 0.9 ft (95 percent range) with no bias.
- Leftover sideways misalignment: 0.2 ft measured; 0.4 ft (one standard deviation) was allowed to be safe.
- Height noise on the bank face: 0.3 ft, which matters more on gentle faces than on steep ones.
Added together for each station (square root of the sum of squares), the limit is 1.3 to 2.2 ft.

## Step 9: every station
<!-- steps: 8 -->

### What the bar chart shows
<!-- steps: 8 -->
The chart shows the south-bank movement at every station from 2011 to 2022. The grey band is the error limit (1.3 to 2.2 ft); a
bar inside it is just noise. Red bars are real movement toward the houses, blue bars are real build-up toward the creek, dark grey
bars are within the noise, and pale bars are set-back banks (not creek erosion).

### Results by section
<!-- steps: 8,9 -->
- West limb (stations 0 to 35): 36 creek-facing stations, typical movement -0.9 ft, largest 0.9 ft. No real change.
- First hump (36 to 57): 4 creek-facing, 17 set back. Station 36 moved +1.7 ft (borderline, limit 1.4 ft); station 38 built up
  -3.0 ft.
- Dip (58 to 75): 8 creek-facing, 10 set back. Real retreat at station 66 (+2.0 ft) and at the active spot, stations 72 (+2.6),
  73 (+6.2), 74 (+9.1) and 75 (+1.5).
- Pool and second hump (76 to 99): 24 creek-facing. No real retreat; build-up at stations 77 (-1.4), 79 (-2.6) and 80 (-2.0).
- East limb (100 to 127): 19 creek-facing, 9 set back. Station 100 moved +1.5 ft (borderline, limit 1.4 ft).
In total 91 stations have a creek-facing bank, 36 are set back and one (station 51) has no clear bank face.

### Changes at set-back banks (not creek erosion)
<!-- steps: 8 -->
Real changes were also measured at some set-back banks, where the creek does not reach: station 39 (-3.1 ft), 44 (+2.4), 55
(+1.8), 57 (+3.5), 60 (-2.0), 63 (-2.8) and 64 (-5.6). Stations 60 to 64 sit next to the terraced yard south of the dip, where fill
was placed between the surveys (the large blue patch on the change map). These are not creek erosion.

### Why build-up (blue) can appear
<!-- steps: 8 -->
A bank moving toward the creek by 1 to 3 ft (stations 38 and 77 to 80) can be real sediment deposition, soil that slumped down
from above and now sits lower on the face, or thick brush that the survey company labelled as ground. It does not affect the
erosion finding.

## Step 10: the answer
<!-- steps: 9 -->

### The main finding
<!-- steps: 9 -->
Along almost the whole M the south bank stayed put (within about 1.5 ft) between November 2011 and April 2022. The one big move is
at stations 72 to 75, where the creek leaves the dip: up to 9.1 ft toward the houses at station 74. A few other spots moved about
2 ft (station 66 by 2.0 ft; stations 36 and 100 by about 1.5 to 1.7 ft, borderline).

### Where exactly the active spot is
<!-- steps: 9 -->
Stations 72 to 75 lie around E 636,480 to 636,520 and N 863,890 to 863,920 (NY State Plane East, ft), on the south bank just
downstream of the dip, at the outside of the bend. The bank face there is 12 to 14 ft high and steep (about 55 to 66 degrees).

### How fast it is moving
<!-- steps: 9 -->
Average rates over the 10.4 years: station 74 about 0.87 ft per year, station 73 about 0.59, station 72 about 0.25, station 75
about 0.15 and station 66 about 0.19 ft per year. These are averages. Banks usually fail in steps during floods, not evenly each
year, so the retreat may have happened in one or two events.

### Why the bank is eroding at stations 72 to 75
<!-- steps: 9 -->
Stations 72 to 75 are on the outside of a bend, where the fastest water is thrown against the bank and scours its foot. The
measurements show the foot of the bank moved more than the top (at station 74: 10.3 ft at the bottom, 7.7 ft at the top), which
is the typical pattern of undercutting followed by slumping. The exact cause (flood events, loss of vegetation, the channel shift
upstream) was not studied.

### What the change map shows
<!-- steps: 9 -->
The change map (2022 minus 2011) shows red where ground was lost and blue where it was gained; changes smaller than the height
error are hidden. Red on the south bank at stations 72 to 75 is the erosion spot. The large blue patch south of the dip is fill
placed for the terraced yard (not the creek). Red along the north bank of the dip is the north bank eroding as the channel moves
north there.

### What happened before the lidar (from the photos)
<!-- steps: 9 -->
The aligned aerial photos show that between 2010 and 2013 a large gravel bar formed on the south side at stations 54 to 66 and
pushed the channel about 15 to 20 ft north, away from the houses. This was most likely during the 2011 floods (Hurricane Irene in
late August and Tropical Storm Lee in early September 2011). Both happened before the first lidar flight (19 November 2011), so
this change is seen on the photos only and is a visual interpretation, not a lidar measurement.

### Recommended next steps
<!-- steps: 9 -->
1. Field check stations 72 to 75: photos, look for undercutting, slumps and exposed roots, and tape the top of bank to fixed
   objects.
2. Put the top of bank from any newer ground survey on the same map as the 2011 and 2022 bank lines, to see whether the retreat
   continued after 2022.
3. Trace the south bank on same-month (spring) aerial photos for every available year to see when the retreat happened.
4. Treat stations 72 to 75 as the priority area for bank protection.

## Assumptions and limits

### Assumptions
<!-- steps: 5,6,7,9 -->
- The houses did not move between 2011 and 2022, and one sideways shift fits the whole study area.
- The survey companies' ground labels are right; thick brush on a bank could be counted as ground.
- The bank face is the tallest stretch steeper than about 8.5 degrees on the south side, limited to its lowest 12 ft.
- The centreline is a fixed ruler built from photos; it is not a surveyed baseline or the deepest point of the channel.

### Limits
<!-- steps: 6,9 -->
- Lidar cannot see under water, so the channel bed and the underwater part of the bank were not measured.
- The 2011 survey has about a quarter of the ground points of 2022, which smooths small bank features (included in the error).
- The result covers only 19 November 2011 to 15 April 2022; changes before or after are not measured.
- Rates are 10-year averages.
- This is a desktop study using public data. It should be checked in the field and against current surveys before design.

### Things that were tried and did not work
<!-- steps: 1,2,3 -->
- Finding the bank edge automatically on the aerial photos failed: tree shadows, rocks and leaf litter make the edge unclear.
- Tracking the channel centreline separately for each photo year was too noisy (year-to-year jumps of several feet even where
  nothing changed), so those results were not used.
- The 1994 photo could not be lined up and the 2004 photo lined up poorly, so neither was used for the centreline.
- The 2010 infrared photo has no coverage at this site.
This is why the measurement relies on lidar, and the photos only provide the ruler and visual checks.

## Tools, files and the assistant

### Software used
<!-- steps: 0 -->
All processing was done in Python: NumPy and SciPy (image matching, shortest path, triangulation, interpolation, statistics),
rasterio (reading and writing georeferenced images), pyproj (coordinate conversion), pyshp (GIS shapefiles), Matplotlib (maps,
charts and the animation frames) and Pillow (images). The lidar files were read with a small reader written for the project, so no
special lidar software was needed.

### Files in the repository
<!-- steps: 0 -->
- analysis/2_Scripts: 01_fetch_imagery.py (downloads the state photos), 02_align_and_transects.py (photo alignment, centreline,
  stations), 04_lidar_south_bank.py (lidar alignment, ground surfaces, bank measurement, error limits, figures),
  05_measure_traced_bank_lines.py (measures bank lines traced by hand, for a future same-month photo comparison).
- analysis/3_GIS: centreline, 10-ft cross lines, study area and the 2011 and 2022 south bank lines, as shapefiles.
- analysis/4_Results: the per-station table (LiDAR_South_Bank_Change.csv), the section summary, the alignment and accuracy table,
  the photo offsets, and the change map, movement chart and cross-section figures.
- docs: this web page, the animation frames and this knowledge base.

### How this assistant works
<!-- steps: 0 -->
The assistant is a retrieval-augmented generation (RAG) assistant. This knowledge base is split into short passages. When someone
asks a question, the page finds the passages that best match the question and the current step of the animation (using a keyword
ranking called BM25), and gives only those passages to an open-source language model with the instruction to answer from them.
By default the model (for example Qwen3.5, Qwen3, Llama 3.1 or Llama 3.2) runs entirely inside the visitor's web browser using
WebLLM and the computer's graphics card (WebGPU), so questions are not sent to any server. The model is downloaded once and then
cached. Visitors can also connect their own model server (any OpenAI-compatible server such as Ollama, LM Studio or llama.cpp) to
use a larger open model. Without a model, the page still answers by showing the best-matching passages. Small models can make
mistakes, so the passages used for each answer are listed under it.

## Glossary

### Terms A to L
<!-- steps: 0,5,6 -->
- Bank face: the steep part of the bank between its toe (bottom) and its top.
- Build-up: the bank moving toward the creek (sediment, slumped soil or dense brush).
- Centreline: the fixed reference line down the middle of the creek used as a ruler.
- Cross line / cross-section: a line square to the creek at a station, and the ground shape along it.
- DEM (digital elevation model): a grid of ground heights, here every 1 ft.
- Detection limit: the smallest movement that can be trusted (95 percent), here 1.3 to 2.2 ft.
- Erosion / retreat: the bank moving away from the creek, toward the houses.
- Lidar: a laser scanner flown in a plane that records the ground as millions of 3-D points.

### Terms M to Z
<!-- steps: 0,1,2,6 -->
- Median: the middle value of a set of numbers; it ignores a few extreme values.
- NAVD88: the vertical datum used for elevations (North American Vertical Datum of 1988), in feet here.
- NMAD: a robust version of the standard deviation that is not thrown off by a few outliers.
- Normalised cross-correlation: the fit score used to match patterns; 1 is a perfect match.
- Orthophoto: an aerial photo corrected so it can be used like a map.
- Outside of a bend: the bank on the outer side of a curve, where the water is fastest and erosion is most likely.
- Set-back bank: a high bank standing behind a raised bar or bench, which the creek does not reach at normal flows.
- State Plane: the NAD83 New York State Plane East coordinate system, in US survey feet (EPSG 2260).
- Station: a point every 10 ft along the centreline, numbered 0 to 127.
- TIN: a triangulated irregular network, the net of triangles joining the lidar ground points.

## Per-station results

<!-- STATION_TABLE_START -->
Movement is 2022 minus 2011 (+ = toward the houses). Distances are from the reference centreline to the bank face at mid-height. Lidar dates: 19 Nov 2011 and 15 Apr 2022 (10.4 years).

### Stations 0 to 9
<!-- steps: 7,8 -->
- Station 0 (0 ft, West limb): creek-facing bank; bank 10.7 ft from the centreline in 2011 and 10.6 ft in 2022; moved -0.5 ft (25/50/75% heights: -0.5, -0.1, -0.9 ft); error limit 1.4 ft; within the noise (no measurable change); -0.05 ft/yr.
- Station 1 (10 ft, West limb): creek-facing bank; bank 13.3 ft from the centreline in 2011 and 13.5 ft in 2022; moved +0.1 ft (25/50/75% heights: 0.0, 0.2, 0.1 ft); error limit 1.4 ft; within the noise (no measurable change); +0.01 ft/yr.
- Station 2 (20 ft, West limb): creek-facing bank; bank 13.7 ft from the centreline in 2011 and 14.3 ft in 2022; moved +0.2 ft (25/50/75% heights: -0.6, 0.6, 0.6 ft); error limit 1.3 ft; within the noise (no measurable change); +0.02 ft/yr.
- Station 3 (30 ft, West limb): creek-facing bank; bank 13.0 ft from the centreline in 2011 and 14.1 ft in 2022; moved +0.9 ft (25/50/75% heights: 1.0, 1.1, 0.6 ft); error limit 1.4 ft; within the noise (no measurable change); +0.09 ft/yr.
- Station 4 (40 ft, West limb): creek-facing bank; bank 13.5 ft from the centreline in 2011 and 13.6 ft in 2022; moved +0.3 ft (25/50/75% heights: -0.2, 0.2, 0.8 ft); error limit 1.5 ft; within the noise (no measurable change); +0.02 ft/yr.
- Station 5 (50 ft, West limb): creek-facing bank; bank 12.6 ft from the centreline in 2011 and 12.3 ft in 2022; moved -0.6 ft (25/50/75% heights: -0.5, -0.3, -1.0 ft); error limit 1.4 ft; within the noise (no measurable change); -0.06 ft/yr.
- Station 6 (60 ft, West limb): creek-facing bank; bank 13.5 ft from the centreline in 2011 and 11.8 ft in 2022; moved -1.4 ft (25/50/75% heights: -1.6, -1.7, -1.0 ft); error limit 1.5 ft; within the noise (no measurable change); -0.14 ft/yr.
- Station 7 (70 ft, West limb): creek-facing bank; bank 15.4 ft from the centreline in 2011 and 15.8 ft in 2022; moved -0.2 ft (25/50/75% heights: -1.2, 0.4, 0.1 ft); error limit 1.4 ft; within the noise (no measurable change); -0.02 ft/yr.
- Station 8 (80 ft, West limb): creek-facing bank; bank 16.3 ft from the centreline in 2011 and 15.1 ft in 2022; moved -1.3 ft (25/50/75% heights: -1.7, -1.1, -1.1 ft); error limit 1.6 ft; within the noise (no measurable change); -0.13 ft/yr.
- Station 9 (90 ft, West limb): creek-facing bank; bank 15.8 ft from the centreline in 2011 and 15.5 ft in 2022; moved -1.2 ft (25/50/75% heights: -1.2, -0.3, -2.0 ft); error limit 1.5 ft; within the noise (no measurable change); -0.11 ft/yr.

### Stations 10 to 19
<!-- steps: 7,8 -->
- Station 10 (100 ft, West limb): creek-facing bank; bank 16.2 ft from the centreline in 2011 and 16.5 ft in 2022; moved -0.1 ft (25/50/75% heights: -0.0, 0.3, -0.5 ft); error limit 1.5 ft; within the noise (no measurable change); -0.01 ft/yr.
- Station 11 (110 ft, West limb): creek-facing bank; bank 14.2 ft from the centreline in 2011 and 12.5 ft in 2022; moved -1.0 ft (25/50/75% heights: -2.5, -1.7, 1.1 ft); error limit 1.5 ft; within the noise (no measurable change); -0.10 ft/yr.
- Station 12 (120 ft, West limb): creek-facing bank; bank 14.9 ft from the centreline in 2011 and 13.2 ft in 2022; moved -1.5 ft (25/50/75% heights: -1.3, -1.7, -1.6 ft); error limit 1.6 ft; within the noise (no measurable change); -0.15 ft/yr.
- Station 13 (130 ft, West limb): creek-facing bank; bank 14.3 ft from the centreline in 2011 and 13.8 ft in 2022; moved -0.3 ft (25/50/75% heights: -0.8, -0.5, 0.5 ft); error limit 1.6 ft; within the noise (no measurable change); -0.03 ft/yr.
- Station 14 (140 ft, West limb): creek-facing bank; bank 15.0 ft from the centreline in 2011 and 13.4 ft in 2022; moved -1.3 ft (25/50/75% heights: -0.1, -1.7, -2.0 ft); error limit 1.4 ft; within the noise (no measurable change); -0.12 ft/yr.
- Station 15 (150 ft, West limb): creek-facing bank; bank 15.1 ft from the centreline in 2011 and 14.3 ft in 2022; moved -0.7 ft (25/50/75% heights: -1.3, -0.8, -0.1 ft); error limit 1.6 ft; within the noise (no measurable change); -0.07 ft/yr.
- Station 16 (160 ft, West limb): creek-facing bank; bank 13.8 ft from the centreline in 2011 and 13.2 ft in 2022; moved -0.9 ft (25/50/75% heights: -0.6, -0.6, -1.4 ft); error limit 1.6 ft; within the noise (no measurable change); -0.08 ft/yr.
- Station 17 (170 ft, West limb): creek-facing bank; bank 12.2 ft from the centreline in 2011 and 10.9 ft in 2022; moved -1.3 ft (25/50/75% heights: -2.1, -1.3, -0.5 ft); error limit 1.6 ft; within the noise (no measurable change); -0.13 ft/yr.
- Station 18 (180 ft, West limb): creek-facing bank; bank 11.2 ft from the centreline in 2011 and 11.0 ft in 2022; moved -0.4 ft (25/50/75% heights: -0.0, -0.2, -0.9 ft); error limit 1.4 ft; within the noise (no measurable change); -0.04 ft/yr.
- Station 19 (190 ft, West limb): creek-facing bank; bank 11.3 ft from the centreline in 2011 and 10.1 ft in 2022; moved -1.1 ft (25/50/75% heights: -1.0, -1.2, -1.1 ft); error limit 1.4 ft; within the noise (no measurable change); -0.11 ft/yr.

### Stations 20 to 29
<!-- steps: 7,8 -->
- Station 20 (200 ft, West limb): creek-facing bank; bank 12.5 ft from the centreline in 2011 and 11.9 ft in 2022; moved -0.4 ft (25/50/75% heights: -0.5, -0.6, -0.2 ft); error limit 1.5 ft; within the noise (no measurable change); -0.04 ft/yr.
- Station 21 (210 ft, West limb): creek-facing bank; bank 14.8 ft from the centreline in 2011 and 13.2 ft in 2022; moved -1.1 ft (25/50/75% heights: -1.2, -1.5, -0.6 ft); error limit 1.6 ft; within the noise (no measurable change); -0.11 ft/yr.
- Station 22 (220 ft, West limb): creek-facing bank; bank 14.0 ft from the centreline in 2011 and 12.9 ft in 2022; moved -1.2 ft (25/50/75% heights: -1.7, -1.0, -1.0 ft); error limit 1.5 ft; within the noise (no measurable change); -0.12 ft/yr.
- Station 23 (230 ft, West limb): creek-facing bank; bank 15.0 ft from the centreline in 2011 and 13.6 ft in 2022; moved -0.7 ft (25/50/75% heights: -0.2, -1.4, -0.5 ft); error limit 1.5 ft; within the noise (no measurable change); -0.07 ft/yr.
- Station 24 (240 ft, West limb): creek-facing bank; bank 14.2 ft from the centreline in 2011 and 13.0 ft in 2022; moved -1.0 ft (25/50/75% heights: -1.2, -1.2, -0.8 ft); error limit 1.5 ft; within the noise (no measurable change); -0.10 ft/yr.
- Station 25 (250 ft, West limb): creek-facing bank; bank 14.2 ft from the centreline in 2011 and 13.2 ft in 2022; moved -1.0 ft (25/50/75% heights: -1.0, -1.0, -1.1 ft); error limit 1.5 ft; within the noise (no measurable change); -0.10 ft/yr.
- Station 26 (260 ft, West limb): creek-facing bank; bank 14.4 ft from the centreline in 2011 and 13.6 ft in 2022; moved -0.7 ft (25/50/75% heights: -0.6, -0.7, -0.7 ft); error limit 1.6 ft; within the noise (no measurable change); -0.06 ft/yr.
- Station 27 (270 ft, West limb): creek-facing bank; bank 14.3 ft from the centreline in 2011 and 13.7 ft in 2022; moved -1.1 ft (25/50/75% heights: -1.8, -0.6, -0.9 ft); error limit 1.6 ft; within the noise (no measurable change); -0.11 ft/yr.
- Station 28 (280 ft, West limb): creek-facing bank; bank 15.9 ft from the centreline in 2011 and 14.4 ft in 2022; moved -1.2 ft (25/50/75% heights: -1.0, -1.5, -1.0 ft); error limit 1.6 ft; within the noise (no measurable change); -0.11 ft/yr.
- Station 29 (290 ft, West limb): creek-facing bank; bank 15.4 ft from the centreline in 2011 and 14.2 ft in 2022; moved -0.9 ft (25/50/75% heights: -0.9, -1.1, -0.7 ft); error limit 1.6 ft; within the noise (no measurable change); -0.09 ft/yr.

### Stations 30 to 39
<!-- steps: 7,8 -->
- Station 30 (300 ft, West limb): creek-facing bank; bank 15.4 ft from the centreline in 2011 and 15.6 ft in 2022; moved -0.5 ft (25/50/75% heights: -0.2, 0.2, -1.6 ft); error limit 1.6 ft; within the noise (no measurable change); -0.05 ft/yr.
- Station 31 (310 ft, West limb): creek-facing bank; bank 15.1 ft from the centreline in 2011 and 14.0 ft in 2022; moved -1.1 ft (25/50/75% heights: -1.1, -1.2, -1.0 ft); error limit 1.5 ft; within the noise (no measurable change); -0.10 ft/yr.
- Station 32 (320 ft, West limb): creek-facing bank; bank 15.9 ft from the centreline in 2011 and 15.0 ft in 2022; moved -0.8 ft (25/50/75% heights: -1.5, -0.9, 0.1 ft); error limit 1.6 ft; within the noise (no measurable change); -0.07 ft/yr.
- Station 33 (330 ft, West limb): creek-facing bank; bank 17.2 ft from the centreline in 2011 and 16.4 ft in 2022; moved +0.2 ft (25/50/75% heights: -0.7, -0.9, 2.1 ft); error limit 1.5 ft; within the noise (no measurable change); +0.02 ft/yr.
- Station 34 (340 ft, West limb): creek-facing bank; bank 18.3 ft from the centreline in 2011 and 17.5 ft in 2022; moved -1.1 ft (25/50/75% heights: -1.1, -0.9, -1.4 ft); error limit 1.5 ft; within the noise (no measurable change); -0.11 ft/yr.
- Station 35 (350 ft, West limb): creek-facing bank; bank 18.8 ft from the centreline in 2011 and 18.3 ft in 2022; moved -0.8 ft (25/50/75% heights: -0.5, -0.4, -1.6 ft); error limit 1.4 ft; within the noise (no measurable change); -0.08 ft/yr.
- Station 36 (360 ft, First hump): creek-facing bank; bank 19.3 ft from the centreline in 2011 and 20.9 ft in 2022; moved +1.7 ft (25/50/75% heights: 3.5, 1.6, -0.1 ft); error limit 1.4 ft; REAL retreat toward the houses; +0.16 ft/yr.
- Station 37 (370 ft, First hump): creek-facing bank; bank 24.5 ft from the centreline in 2011 and 25.8 ft in 2022; moved +0.4 ft (25/50/75% heights: 0.3, 1.3, -0.4 ft); error limit 1.6 ft; within the noise (no measurable change); +0.04 ft/yr.
- Station 38 (380 ft, First hump): creek-facing bank; bank 43.6 ft from the centreline in 2011 and 40.3 ft in 2022; moved -3.0 ft (25/50/75% heights: -3.1, -3.4, -2.5 ft); error limit 1.7 ft; REAL build-up toward the creek; -0.29 ft/yr.
- Station 39 (390 ft, First hump): bank set back 44 ft behind a raised bar or bench; bank 50.7 ft from the centreline in 2011 and 47.6 ft in 2022; moved -3.1 ft (25/50/75% heights: -0.0, -3.1, -6.3 ft); error limit 1.3 ft; real change, but at a set-back bank (not creek erosion); -0.30 ft/yr.

### Stations 40 to 49
<!-- steps: 7,8 -->
- Station 40 (400 ft, First hump): bank set back 50 ft behind a raised bar or bench; bank 56.2 ft from the centreline in 2011 and 55.9 ft in 2022; moved +0.0 ft (25/50/75% heights: 0.2, -0.3, 0.2 ft); error limit 1.6 ft; within the noise, set-back bank; +0.00 ft/yr.
- Station 41 (410 ft, First hump): bank set back 50 ft behind a raised bar or bench; bank 60.6 ft from the centreline in 2011 and 61.4 ft in 2022; moved +0.7 ft (25/50/75% heights: 0.2, 0.7, 1.3 ft); error limit 2.1 ft; within the noise, set-back bank; +0.07 ft/yr.
- Station 42 (420 ft, First hump): bank set back 55 ft behind a raised bar or bench; bank 63.2 ft from the centreline in 2011 and 63.8 ft in 2022; moved +0.6 ft (25/50/75% heights: 0.4, 0.6, 0.6 ft); error limit 1.8 ft; within the noise, set-back bank; +0.05 ft/yr.
- Station 43 (430 ft, First hump): bank set back 60 ft behind a raised bar or bench; bank 64.6 ft from the centreline in 2011 and 65.2 ft in 2022; moved +1.2 ft (25/50/75% heights: 1.1, 0.6, 1.9 ft); error limit 1.8 ft; within the noise, set-back bank; +0.11 ft/yr.
- Station 44 (440 ft, First hump): bank set back 58 ft behind a raised bar or bench; bank 64.9 ft from the centreline in 2011 and 66.7 ft in 2022; moved +2.4 ft (25/50/75% heights: 3.3, 1.8, 2.1 ft); error limit 2.0 ft; real change, but at a set-back bank (not creek erosion); +0.23 ft/yr.
- Station 45 (450 ft, First hump): bank set back 62 ft behind a raised bar or bench; bank 70.7 ft from the centreline in 2011 and 70.5 ft in 2022; moved +0.4 ft (25/50/75% heights: 1.4, -0.3, 0.1 ft); error limit 2.1 ft; within the noise, set-back bank; +0.04 ft/yr.
- Station 46 (460 ft, First hump): bank set back 65 ft behind a raised bar or bench; bank 70.6 ft from the centreline in 2011 and 72.4 ft in 2022; moved +0.9 ft (25/50/75% heights: 1.8, 1.8, -0.9 ft); error limit 2.2 ft; within the noise, set-back bank; +0.09 ft/yr.
- Station 47 (470 ft, First hump): bank set back 67 ft behind a raised bar or bench; bank 71.8 ft from the centreline in 2011 and 73.0 ft in 2022; moved +0.7 ft (25/50/75% heights: 1.5, 1.2, -0.7 ft); error limit 2.0 ft; within the noise, set-back bank; +0.06 ft/yr.
- Station 48 (480 ft, First hump): bank set back 68 ft behind a raised bar or bench; bank 73.8 ft from the centreline in 2011 and 73.6 ft in 2022; moved -0.5 ft (25/50/75% heights: -1.1, -0.1, -0.4 ft); error limit 1.9 ft; within the noise, set-back bank; -0.05 ft/yr.
- Station 49 (490 ft, First hump): bank set back 66 ft behind a raised bar or bench; bank 74.9 ft from the centreline in 2011 and 75.1 ft in 2022; moved -0.1 ft (25/50/75% heights: 0.5, 0.1, -0.8 ft); error limit 2.1 ft; within the noise, set-back bank; -0.01 ft/yr.

### Stations 50 to 59
<!-- steps: 7,8 -->
- Station 50 (500 ft, First hump): bank set back 66 ft behind a raised bar or bench; bank 76.6 ft from the centreline in 2011 and 76.4 ft in 2022; moved +0.3 ft (25/50/75% heights: 1.4, -0.2, -0.4 ft); error limit 2.0 ft; within the noise, set-back bank; +0.03 ft/yr.
- Station 51 (510 ft, First hump): no clear bank face on the 2022 cross-section, not measured.
- Station 52 (520 ft, First hump): creek-facing bank; bank 18.3 ft from the centreline in 2011 and 17.3 ft in 2022; moved -1.6 ft (25/50/75% heights: 1.3, -1.0, -5.0 ft); error limit 2.1 ft; within the noise (no measurable change); -0.15 ft/yr.
- Station 53 (530 ft, First hump): bank set back 69 ft behind a raised bar or bench; bank 72.3 ft from the centreline in 2011 and 74.7 ft in 2022; moved +1.6 ft (25/50/75% heights: 0.8, 2.3, 1.7 ft); error limit 2.2 ft; within the noise, set-back bank; +0.15 ft/yr.
- Station 54 (540 ft, First hump): bank set back 70 ft behind a raised bar or bench; bank 75.0 ft from the centreline in 2011 and 76.3 ft in 2022; moved +0.8 ft (25/50/75% heights: 0.6, 1.2, 0.5 ft); error limit 1.9 ft; within the noise, set-back bank; +0.07 ft/yr.
- Station 55 (550 ft, First hump): bank set back 70 ft behind a raised bar or bench; bank 74.0 ft from the centreline in 2011 and 75.6 ft in 2022; moved +1.8 ft (25/50/75% heights: 1.8, 1.6, 2.0 ft); error limit 1.7 ft; real change, but at a set-back bank (not creek erosion); +0.17 ft/yr.
- Station 56 (560 ft, First hump): bank set back 68 ft behind a raised bar or bench; bank 74.3 ft from the centreline in 2011 and 75.7 ft in 2022; moved +0.5 ft (25/50/75% heights: 0.3, 1.4, -0.3 ft); error limit 1.6 ft; within the noise, set-back bank; +0.04 ft/yr.
- Station 57 (570 ft, First hump): bank set back 62 ft behind a raised bar or bench; bank 68.7 ft from the centreline in 2011 and 72.4 ft in 2022; moved +3.5 ft (25/50/75% heights: 2.6, 3.7, 4.3 ft); error limit 1.7 ft; real change, but at a set-back bank (not creek erosion); +0.34 ft/yr.
- Station 58 (580 ft, Dip): bank set back 68 ft behind a raised bar or bench; bank 73.1 ft from the centreline in 2011 and 73.2 ft in 2022; moved +0.2 ft (25/50/75% heights: 0.4, 0.1, 0.0 ft); error limit 1.6 ft; within the noise, set-back bank; +0.02 ft/yr.
- Station 59 (590 ft, Dip): bank set back 58 ft behind a raised bar or bench; bank 71.8 ft from the centreline in 2011 and 72.9 ft in 2022; moved +1.1 ft (25/50/75% heights: 0.3, 1.1, 1.9 ft); error limit 1.5 ft; within the noise, set-back bank; +0.11 ft/yr.

### Stations 60 to 69
<!-- steps: 7,8 -->
- Station 60 (600 ft, Dip): bank set back 56 ft behind a raised bar or bench; bank 70.2 ft from the centreline in 2011 and 67.7 ft in 2022; moved -2.0 ft (25/50/75% heights: -1.8, -2.5, -1.8 ft); error limit 1.8 ft; real change, but at a set-back bank (not creek erosion); -0.20 ft/yr.
- Station 61 (610 ft, Dip): bank set back 56 ft behind a raised bar or bench; bank 67.3 ft from the centreline in 2011 and 67.3 ft in 2022; moved -0.5 ft (25/50/75% heights: -1.5, -0.0, 0.2 ft); error limit 1.5 ft; within the noise, set-back bank; -0.04 ft/yr.
- Station 62 (620 ft, Dip): bank set back 58 ft behind a raised bar or bench; bank 66.1 ft from the centreline in 2011 and 66.6 ft in 2022; moved +0.3 ft (25/50/75% heights: -0.8, 0.6, 1.1 ft); error limit 1.5 ft; within the noise, set-back bank; +0.03 ft/yr.
- Station 63 (630 ft, Dip): bank set back 48 ft behind a raised bar or bench; bank 61.2 ft from the centreline in 2011 and 58.8 ft in 2022; moved -2.8 ft (25/50/75% heights: -3.6, -2.3, -2.3 ft); error limit 1.7 ft; real change, but at a set-back bank (not creek erosion); -0.27 ft/yr.
- Station 64 (640 ft, Dip): bank set back 40 ft behind a raised bar or bench; bank 58.7 ft from the centreline in 2011 and 53.0 ft in 2022; moved -5.6 ft (25/50/75% heights: -5.4, -5.7, -5.8 ft); error limit 1.5 ft; real change, but at a set-back bank (not creek erosion); -0.54 ft/yr.
- Station 65 (650 ft, Dip): bank set back 42 ft behind a raised bar or bench; bank 50.1 ft from the centreline in 2011 and 50.2 ft in 2022; moved -0.3 ft (25/50/75% heights: -0.2, 0.0, -0.8 ft); error limit 1.5 ft; within the noise, set-back bank; -0.03 ft/yr.
- Station 66 (660 ft, Dip): creek-facing bank; bank 41.4 ft from the centreline in 2011 and 43.2 ft in 2022; moved +2.0 ft (25/50/75% heights: 1.8, 1.8, 2.4 ft); error limit 1.5 ft; REAL retreat toward the houses; +0.19 ft/yr.
- Station 67 (670 ft, Dip): no clear bank face on the 2022 cross-section, not measured.
- Station 68 (680 ft, Dip): bank set back 52 ft behind a raised bar or bench; bank 65.8 ft from the centreline in 2011 and 65.0 ft in 2022; moved -1.1 ft (25/50/75% heights: -0.5, -0.8, -2.0 ft); error limit 1.5 ft; within the noise, set-back bank; -0.11 ft/yr.
- Station 69 (690 ft, Dip): creek-facing bank; bank 33.0 ft from the centreline in 2011 and 32.3 ft in 2022; moved -0.6 ft (25/50/75% heights: -0.4, -0.7, -0.5 ft); error limit 1.4 ft; within the noise (no measurable change); -0.05 ft/yr.

### Stations 70 to 79
<!-- steps: 7,8 -->
- Station 70 (700 ft, Dip): creek-facing bank; bank 32.8 ft from the centreline in 2011 and 31.5 ft in 2022; moved -1.0 ft (25/50/75% heights: -0.3, -1.3, -1.4 ft); error limit 1.3 ft; within the noise (no measurable change); -0.09 ft/yr.
- Station 71 (710 ft, Dip): creek-facing bank; bank 27.3 ft from the centreline in 2011 and 25.9 ft in 2022; moved -0.7 ft (25/50/75% heights: -0.1, -1.4, -0.5 ft); error limit 1.4 ft; within the noise (no measurable change); -0.06 ft/yr.
- Station 72 (720 ft, Dip): creek-facing bank; bank 21.7 ft from the centreline in 2011 and 24.2 ft in 2022; moved +2.6 ft (25/50/75% heights: 4.6, 2.5, 0.6 ft); error limit 1.3 ft; REAL retreat toward the houses; +0.25 ft/yr.
- Station 73 (730 ft, Dip): creek-facing bank; bank 20.6 ft from the centreline in 2011 and 27.0 ft in 2022; moved +6.2 ft (25/50/75% heights: 7.0, 6.4, 5.1 ft); error limit 1.3 ft; REAL retreat toward the houses; +0.59 ft/yr.
- Station 74 (740 ft, Dip): creek-facing bank; bank 20.3 ft from the centreline in 2011 and 29.6 ft in 2022; moved +9.1 ft (25/50/75% heights: 10.3, 9.3, 7.7 ft); error limit 1.3 ft; REAL retreat toward the houses; +0.87 ft/yr.
- Station 75 (750 ft, Dip): creek-facing bank; bank 23.5 ft from the centreline in 2011 and 25.3 ft in 2022; moved +1.5 ft (25/50/75% heights: 1.6, 1.8, 1.1 ft); error limit 1.3 ft; REAL retreat toward the houses; +0.15 ft/yr.
- Station 76 (760 ft, Pool / second hump): creek-facing bank; bank 23.0 ft from the centreline in 2011 and 23.1 ft in 2022; moved -0.5 ft (25/50/75% heights: -1.3, 0.1, -0.4 ft); error limit 1.3 ft; within the noise (no measurable change); -0.05 ft/yr.
- Station 77 (770 ft, Pool / second hump): creek-facing bank; bank 22.0 ft from the centreline in 2011 and 20.5 ft in 2022; moved -1.4 ft (25/50/75% heights: 1.0, -1.5, -3.6 ft); error limit 1.3 ft; REAL build-up toward the creek; -0.13 ft/yr.
- Station 78 (780 ft, Pool / second hump): creek-facing bank; bank 19.5 ft from the centreline in 2011 and 19.5 ft in 2022; moved -0.7 ft (25/50/75% heights: 0.9, -0.0, -3.0 ft); error limit 1.3 ft; within the noise (no measurable change); -0.07 ft/yr.
- Station 79 (790 ft, Pool / second hump): creek-facing bank; bank 23.6 ft from the centreline in 2011 and 21.0 ft in 2022; moved -2.6 ft (25/50/75% heights: -0.1, -2.6, -5.2 ft); error limit 1.3 ft; REAL build-up toward the creek; -0.25 ft/yr.

### Stations 80 to 89
<!-- steps: 7,8 -->
- Station 80 (800 ft, Pool / second hump): creek-facing bank; bank 24.0 ft from the centreline in 2011 and 22.2 ft in 2022; moved -2.0 ft (25/50/75% heights: -0.6, -1.8, -3.5 ft); error limit 1.3 ft; REAL build-up toward the creek; -0.19 ft/yr.
- Station 81 (810 ft, Pool / second hump): creek-facing bank; bank 32.2 ft from the centreline in 2011 and 32.6 ft in 2022; moved +0.2 ft (25/50/75% heights: 0.3, 0.3, 0.1 ft); error limit 1.5 ft; within the noise (no measurable change); +0.02 ft/yr.
- Station 82 (820 ft, Pool / second hump): creek-facing bank; bank 37.2 ft from the centreline in 2011 and 36.7 ft in 2022; moved -0.2 ft (25/50/75% heights: 0.7, -0.6, -0.8 ft); error limit 1.5 ft; within the noise (no measurable change); -0.02 ft/yr.
- Station 83 (830 ft, Pool / second hump): creek-facing bank; bank 39.4 ft from the centreline in 2011 and 40.3 ft in 2022; moved +0.9 ft (25/50/75% heights: 1.3, 0.9, 0.6 ft); error limit 1.5 ft; within the noise (no measurable change); +0.09 ft/yr.
- Station 84 (840 ft, Pool / second hump): creek-facing bank; bank 41.0 ft from the centreline in 2011 and 43.4 ft in 2022; moved +0.8 ft (25/50/75% heights: -0.4, 2.4, 0.6 ft); error limit 1.5 ft; within the noise (no measurable change); +0.08 ft/yr.
- Station 85 (850 ft, Pool / second hump): creek-facing bank; bank 43.6 ft from the centreline in 2011 and 44.6 ft in 2022; moved +1.1 ft (25/50/75% heights: 1.3, 1.0, 0.8 ft); error limit 1.5 ft; within the noise (no measurable change); +0.10 ft/yr.
- Station 86 (860 ft, Pool / second hump): creek-facing bank; bank 45.5 ft from the centreline in 2011 and 45.9 ft in 2022; moved +1.1 ft (25/50/75% heights: 2.1, 0.4, 0.7 ft); error limit 1.5 ft; within the noise (no measurable change); +0.10 ft/yr.
- Station 87 (870 ft, Pool / second hump): creek-facing bank; bank 45.8 ft from the centreline in 2011 and 46.0 ft in 2022; moved -0.0 ft (25/50/75% heights: -1.0, 0.2, 0.8 ft); error limit 1.5 ft; within the noise (no measurable change); -0.00 ft/yr.
- Station 88 (880 ft, Pool / second hump): creek-facing bank; bank 47.7 ft from the centreline in 2011 and 48.6 ft in 2022; moved +0.9 ft (25/50/75% heights: 1.1, 0.8, 0.7 ft); error limit 1.4 ft; within the noise (no measurable change); +0.09 ft/yr.
- Station 89 (890 ft, Pool / second hump): creek-facing bank; bank 49.6 ft from the centreline in 2011 and 50.0 ft in 2022; moved +0.5 ft (25/50/75% heights: 0.6, 0.3, 0.5 ft); error limit 1.4 ft; within the noise (no measurable change); +0.05 ft/yr.

### Stations 90 to 99
<!-- steps: 7,8 -->
- Station 90 (900 ft, Pool / second hump): creek-facing bank; bank 50.5 ft from the centreline in 2011 and 50.6 ft in 2022; moved +0.3 ft (25/50/75% heights: 0.3, 0.1, 0.4 ft); error limit 1.4 ft; within the noise (no measurable change); +0.03 ft/yr.
- Station 91 (910 ft, Pool / second hump): creek-facing bank; bank 49.2 ft from the centreline in 2011 and 49.8 ft in 2022; moved +0.6 ft (25/50/75% heights: 0.1, 0.6, 1.2 ft); error limit 1.5 ft; within the noise (no measurable change); +0.06 ft/yr.
- Station 92 (920 ft, Pool / second hump): creek-facing bank; bank 50.9 ft from the centreline in 2011 and 51.5 ft in 2022; moved +0.0 ft (25/50/75% heights: -1.4, 0.7, 0.7 ft); error limit 1.5 ft; within the noise (no measurable change); +0.00 ft/yr.
- Station 93 (930 ft, Pool / second hump): creek-facing bank; bank 55.4 ft from the centreline in 2011 and 56.6 ft in 2022; moved +0.6 ft (25/50/75% heights: 0.2, 1.2, 0.4 ft); error limit 1.4 ft; within the noise (no measurable change); +0.06 ft/yr.
- Station 94 (940 ft, Pool / second hump): creek-facing bank; bank 51.7 ft from the centreline in 2011 and 52.4 ft in 2022; moved +1.0 ft (25/50/75% heights: 1.6, 0.7, 0.6 ft); error limit 1.4 ft; within the noise (no measurable change); +0.09 ft/yr.
- Station 95 (950 ft, Pool / second hump): creek-facing bank; bank 48.4 ft from the centreline in 2011 and 49.8 ft in 2022; moved +0.7 ft (25/50/75% heights: 0.3, 1.5, 0.5 ft); error limit 1.5 ft; within the noise (no measurable change); +0.07 ft/yr.
- Station 96 (960 ft, Pool / second hump): creek-facing bank; bank 43.6 ft from the centreline in 2011 and 43.5 ft in 2022; moved +0.3 ft (25/50/75% heights: 1.7, -0.1, -0.7 ft); error limit 1.4 ft; within the noise (no measurable change); +0.03 ft/yr.
- Station 97 (970 ft, Pool / second hump): creek-facing bank; bank 44.7 ft from the centreline in 2011 and 44.1 ft in 2022; moved -0.5 ft (25/50/75% heights: 0.2, -0.6, -1.0 ft); error limit 1.4 ft; within the noise (no measurable change); -0.05 ft/yr.
- Station 98 (980 ft, Pool / second hump): creek-facing bank; bank 42.3 ft from the centreline in 2011 and 43.0 ft in 2022; moved +0.0 ft (25/50/75% heights: 0.1, 0.7, -0.7 ft); error limit 1.4 ft; within the noise (no measurable change); +0.00 ft/yr.
- Station 99 (990 ft, Pool / second hump): creek-facing bank; bank 41.7 ft from the centreline in 2011 and 41.0 ft in 2022; moved -0.9 ft (25/50/75% heights: -0.8, -0.6, -1.3 ft); error limit 1.3 ft; within the noise (no measurable change); -0.09 ft/yr.

### Stations 100 to 109
<!-- steps: 7,8 -->
- Station 100 (1000 ft, East limb): creek-facing bank; bank 38.8 ft from the centreline in 2011 and 39.9 ft in 2022; moved +1.5 ft (25/50/75% heights: 3.1, 1.1, 0.3 ft); error limit 1.4 ft; REAL retreat toward the houses; +0.15 ft/yr.
- Station 101 (1010 ft, East limb): creek-facing bank; bank 36.2 ft from the centreline in 2011 and 38.0 ft in 2022; moved +1.2 ft (25/50/75% heights: 1.2, 1.8, 0.7 ft); error limit 1.4 ft; within the noise (no measurable change); +0.11 ft/yr.
- Station 102 (1020 ft, East limb): creek-facing bank; bank 36.0 ft from the centreline in 2011 and 36.9 ft in 2022; moved +0.9 ft (25/50/75% heights: 1.7, 0.9, 0.1 ft); error limit 1.3 ft; within the noise (no measurable change); +0.09 ft/yr.
- Station 103 (1030 ft, East limb): creek-facing bank; bank 37.0 ft from the centreline in 2011 and 37.4 ft in 2022; moved +0.4 ft (25/50/75% heights: 1.1, 0.4, -0.3 ft); error limit 1.3 ft; within the noise (no measurable change); +0.04 ft/yr.
- Station 104 (1040 ft, East limb): creek-facing bank; bank 39.1 ft from the centreline in 2011 and 38.8 ft in 2022; moved +0.2 ft (25/50/75% heights: 0.9, -0.3, 0.1 ft); error limit 1.4 ft; within the noise (no measurable change); +0.02 ft/yr.
- Station 105 (1050 ft, East limb): creek-facing bank; bank 40.9 ft from the centreline in 2011 and 41.1 ft in 2022; moved +0.0 ft (25/50/75% heights: 0.5, 0.2, -0.5 ft); error limit 1.4 ft; within the noise (no measurable change); +0.00 ft/yr.
- Station 106 (1060 ft, East limb): creek-facing bank; bank 43.3 ft from the centreline in 2011 and 42.1 ft in 2022; moved -0.1 ft (25/50/75% heights: 1.1, -1.2, -0.1 ft); error limit 1.6 ft; within the noise (no measurable change); -0.01 ft/yr.
- Station 107 (1070 ft, East limb): creek-facing bank; bank 41.0 ft from the centreline in 2011 and 41.3 ft in 2022; moved -0.0 ft (25/50/75% heights: -1.0, 0.3, 0.6 ft); error limit 1.6 ft; within the noise (no measurable change); -0.00 ft/yr.
- Station 108 (1080 ft, East limb): creek-facing bank; bank 45.3 ft from the centreline in 2011 and 45.2 ft in 2022; moved +0.0 ft (25/50/75% heights: 0.2, -0.1, -0.1 ft); error limit 1.5 ft; within the noise (no measurable change); +0.00 ft/yr.
- Station 109 (1090 ft, East limb): creek-facing bank; bank 43.5 ft from the centreline in 2011 and 42.3 ft in 2022; moved -0.4 ft (25/50/75% heights: 0.4, -1.2, -0.3 ft); error limit 1.4 ft; within the noise (no measurable change); -0.04 ft/yr.

### Stations 110 to 119
<!-- steps: 7,8 -->
- Station 110 (1100 ft, East limb): creek-facing bank; bank 38.2 ft from the centreline in 2011 and 38.2 ft in 2022; moved -0.0 ft (25/50/75% heights: 1.3, 0.0, -1.4 ft); error limit 1.5 ft; within the noise (no measurable change); -0.00 ft/yr.
- Station 111 (1110 ft, East limb): creek-facing bank; bank 37.3 ft from the centreline in 2011 and 37.1 ft in 2022; moved +0.5 ft (25/50/75% heights: 1.2, -0.2, 0.3 ft); error limit 1.4 ft; within the noise (no measurable change); +0.04 ft/yr.
- Station 112 (1120 ft, East limb): creek-facing bank; bank 37.6 ft from the centreline in 2011 and 38.7 ft in 2022; moved +0.7 ft (25/50/75% heights: 1.8, 1.1, -0.7 ft); error limit 1.6 ft; within the noise (no measurable change); +0.07 ft/yr.
- Station 113 (1130 ft, East limb): creek-facing bank; bank 54.2 ft from the centreline in 2011 and 53.7 ft in 2022; moved -0.3 ft (25/50/75% heights: 0.2, -0.5, -0.4 ft); error limit 1.7 ft; within the noise (no measurable change); -0.02 ft/yr.
- Station 114 (1140 ft, East limb): bank set back 36 ft behind a raised bar or bench; bank 56.9 ft from the centreline in 2011 and 57.0 ft in 2022; moved +0.1 ft (25/50/75% heights: -0.1, 0.1, 0.2 ft); error limit 1.6 ft; within the noise, set-back bank; +0.01 ft/yr.
- Station 115 (1150 ft, East limb): creek-facing bank; bank 58.4 ft from the centreline in 2011 and 58.6 ft in 2022; moved +0.0 ft (25/50/75% heights: 0.3, 0.3, -0.5 ft); error limit 1.6 ft; within the noise (no measurable change); +0.00 ft/yr.
- Station 116 (1160 ft, East limb): creek-facing bank; bank 51.8 ft from the centreline in 2011 and 51.7 ft in 2022; moved +0.2 ft (25/50/75% heights: -0.1, -0.2, 0.9 ft); error limit 1.7 ft; within the noise (no measurable change); +0.02 ft/yr.
- Station 117 (1170 ft, East limb): creek-facing bank; bank 52.9 ft from the centreline in 2011 and 52.5 ft in 2022; moved +0.5 ft (25/50/75% heights: 1.0, -0.4, 0.9 ft); error limit 1.6 ft; within the noise (no measurable change); +0.05 ft/yr.
- Station 118 (1180 ft, East limb): creek-facing bank; bank 56.0 ft from the centreline in 2011 and 55.9 ft in 2022; moved -0.1 ft (25/50/75% heights: -0.2, -0.1, 0.1 ft); error limit 1.5 ft; within the noise (no measurable change); -0.01 ft/yr.
- Station 119 (1190 ft, East limb): creek-facing bank; bank 60.6 ft from the centreline in 2011 and 60.7 ft in 2022; moved +0.2 ft (25/50/75% heights: 0.1, 0.1, 0.4 ft); error limit 1.6 ft; within the noise (no measurable change); +0.02 ft/yr.

### Stations 120 to 127
<!-- steps: 7,8 -->
- Station 120 (1200 ft, East limb): bank set back 52 ft behind a raised bar or bench; bank 61.9 ft from the centreline in 2011 and 62.0 ft in 2022; moved +0.0 ft (25/50/75% heights: 0.0, 0.1, -0.0 ft); error limit 1.6 ft; within the noise, set-back bank; +0.00 ft/yr.
- Station 121 (1210 ft, East limb): bank set back 35 ft behind a raised bar or bench; bank 63.7 ft from the centreline in 2011 and 64.3 ft in 2022; moved +0.6 ft (25/50/75% heights: 0.6, 0.6, 0.7 ft); error limit 1.6 ft; within the noise, set-back bank; +0.06 ft/yr.
- Station 122 (1220 ft, East limb): bank set back 36 ft behind a raised bar or bench; bank 64.8 ft from the centreline in 2011 and 65.2 ft in 2022; moved +0.4 ft (25/50/75% heights: 1.0, 0.3, -0.1 ft); error limit 1.5 ft; within the noise, set-back bank; +0.04 ft/yr.
- Station 123 (1230 ft, East limb): bank set back 26 ft behind a raised bar or bench; bank 66.6 ft from the centreline in 2011 and 66.3 ft in 2022; moved +0.3 ft (25/50/75% heights: 1.2, -0.3, 0.0 ft); error limit 1.5 ft; within the noise, set-back bank; +0.03 ft/yr.
- Station 124 (1240 ft, East limb): bank set back 30 ft behind a raised bar or bench; bank 70.0 ft from the centreline in 2011 and 69.8 ft in 2022; moved -0.7 ft (25/50/75% heights: -2.3, -0.2, 0.4 ft); error limit 1.5 ft; within the noise, set-back bank; -0.07 ft/yr.
- Station 125 (1250 ft, East limb): bank set back 28 ft behind a raised bar or bench; bank 69.7 ft from the centreline in 2011 and 69.7 ft in 2022; moved -0.2 ft (25/50/75% heights: -1.5, -0.0, 0.8 ft); error limit 1.5 ft; within the noise, set-back bank; -0.02 ft/yr.
- Station 126 (1260 ft, East limb): bank set back 31 ft behind a raised bar or bench; bank 69.7 ft from the centreline in 2011 and 70.2 ft in 2022; moved +0.1 ft (25/50/75% heights: -0.7, 0.4, 0.7 ft); error limit 1.6 ft; within the noise, set-back bank; +0.01 ft/yr.
- Station 127 (1270 ft, East limb): bank set back 26 ft behind a raised bar or bench; bank 68.9 ft from the centreline in 2011 and 69.4 ft in 2022; moved +0.0 ft (25/50/75% heights: -1.1, 0.5, 0.6 ft); error limit 1.5 ft; within the noise, set-back bank; +0.00 ft/yr.
<!-- STATION_TABLE_END -->

## Data credits

### Sources and credits
<!-- steps: 0,5 -->
- Aerial photos: New York State Statewide Digital Orthoimagery Program, NYS ITS Geospatial Services (orthos.its.ny.gov).
- 2011 lidar: U.S. Geological Survey, Northeast lidar project (ARRA_LFTNE_NEWYORK_2010), via the NYS GIS Clearinghouse.
- 2022 lidar: New York State Southeast 4 County 2022 lidar project, via the NYS GIS Clearinghouse (gisdata.ny.gov).
