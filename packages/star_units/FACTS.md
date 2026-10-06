# Published values the tests of star_units may cite (checked by the reviewer against the computation)

All of these are EXACT by definition (SI Brochure 9th edition; NIST Special Publication 811; the international yard and pound
agreement of 1959; standard gravity; IAU 2012 Resolution B2 and IAU 2015 Resolution B2). convert(1.0, unit, SI unit) must return
exactly the float nearest to the value given (use ==, or relative 1e-15 where a product is involved):
- length: 1 in = 0.0254 m; 1 ft = 0.3048 m; 1 yd = 0.9144 m; 1 mi = 1609.344 m; 1 nmi = 1852 m; 1 au = 149597870700 m;
  1 ly = 9460730472580800 m (c = 299792458 m/s times a Julian year of 31557600 s); 1 pc = 648000 / pi au = 3.0856775814913673e16 m (relative 1e-15);
- mass: 1 lb = 0.45359237 kg; 1 oz = 1/16 lb = 0.028349523125 kg; 1 slug = 1 lbf s2/ft = 14.593902937206364 kg; 1 t = 1000 kg;
- force: 1 kgf = 9.80665 N; 1 lbf = 0.45359237 * 9.80665 = 4.4482216152605 N; 1 dyn = 1e-5 N;
- pressure: 1 atm = 101325 Pa; 1 bar = 1e5 Pa; 1 torr = 101325 / 760 Pa; 1 psi = 1 lbf / in2 = 6894.757293168362 Pa (relative 1e-15);
- speed: 1 kn = 1852 / 3600 m/s; 1 mph = 0.44704 m/s; 1 km/h = 1 / 3.6 m/s;
- energy: 1 eV = 1.602176634e-19 J; 1 cal = 4.184 J (thermochemical); 1 BTU = 1055.05585262 J (International Table); 1 Wh = 3600 J; 1 erg = 1e-7 J;
  1 ft*lbf = 1.3558179483314004 J;
- power: 1 hp = 550 ft*lbf/s = 745.6998715822702 W (relative 1e-15);
- time: 1 day = 86400 s; 1 week = 604800 s; 1 julian_year = 365.25 days = 31557600 s;
- angle: 180 deg = pi rad; 1 deg = 60 arcmin = 3600 arcsec = 3600000 mas; 1 rev = 360 deg = 2 pi rad (relative 1e-15);
- temperature: 0 degC = 273.15 K = 32 degF = 491.67 degR; 100 degC = 212 degF; -40 degC = -40 degF; 0 K = -273.15 degC = -459.67 degF.

Behaviour of the module (state it; do not call it published):
- dimension(unit) returns one of: angle, energy, force, impulse, length, mass, power, pressure, speed, time, temperature;
  units() lists all 68 names sorted; units("impulse") == ["N*s", "kN*s", "lbf*s"]; units("temperature") == ["K", "degC", "degF", "degR"];
- converting a unit to itself returns the value unchanged (exactly); convert(v, a, b) * convert(1, b, a) == v within 2e-16 relative;
  convert is linear in the value; convert(v, a, c) == convert(convert(v, a, b), b, c) within 4e-16 relative for units of one dimension;
- different dimensions are refused with a message that names both dimensions: convert(1, "lbf", "N*s") (force vs impulse: the Mars Climate Orbiter
  confusion was pound-force seconds read as newton seconds; here 1 lbf*s = 4.4482216152605 N*s and the two unit names are different),
  convert(1, "lb", "lbf") (mass vs force), convert(1, "deg", "m"), and convert(1, "K", "m") / convert(1, "degC", "K") (temperatures are converted
  only by convert_temperature: convert raises "unknown unit" for them);
- unit names are case-sensitive: "M", "Km", "LBF", "n" are unknown; a unit must be a str (None, 1, b"m", ["m"] are refused);
- the value must be a finite real number: True, False, "1", None, nan, inf, 1j, [1.0] are refused; ints and fractions.Fraction are accepted;
  a result that overflows a float is refused: convert(1e308, "km", "mm");
- temperatures: below absolute zero is refused (convert_temperature(-1, "K", "degC"), convert_temperature(-273.16, "degC", "K"),
  convert_temperature(-459.68, "degF", "K")); absolute zero itself survives a round trip through a float:
  convert_temperature(convert_temperature(0, "K", "degC"), "degC", "K") is within 1e-12 of 0 and is not negative;
  convert_temperature uses only the four temperature names ("m" is an unknown temperature unit).
