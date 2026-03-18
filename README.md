# ⚡ tunti-vs-vartti

> **Does 15-minute spot price granularity actually save you money over 1-hour slots?**  
> A Finnish electricity pricing optimizer that answers this question — with hard numbers.

---

## What is this?

Finnish electricity consumers on spot-price contracts (pörssisähkö) can schedule flexible loads — EV charging, water heaters, heat pumps — to run during the cheapest hours. Most scheduling tools work on **1-hour granularity**. But the Nordic spot market publishes prices at **15-minute resolution** too.

This tool compares three strategies side-by-side for any given energy load:

| Strategy | Description |
|---|---|
| **Optimi 1h** | Pick the N cheapest full hours of the day |
| **Optimi 15min** | Pick the N×4 cheapest 15-minute slots of the day |
| **No Brains** *(optional)* | Fixed schedule: 22→23→00→01→... (cheapest-first by assumption) |

Data is fetched live from [spot-hinta.fi](https://spot-hinta.fi) for today and tomorrow. All prices include **VAT, transfer fees (day/night rates), and your supplier's margin**.

---

## Example output

```
--- TÄNÄÄN (12.0 kWh / 5 h) ---
  Skenaario      Hinta   s/kWh                          Ajat
  Optimi 1h   0.4521 €   3.77   01:00, 02:00, 03:00, 04:00, 05:00
 Optimi 15min  0.4388 €   3.66              Vartti-optimointi
   No Brains   0.5103 €   4.25   22:00, 23:00, 00:00, 01:00, 02:00

>> OPTIMOINNIN HYÖTY (B vs C): 0.0715 € (14.0 %)
--------------------------------------------------

--- HUOMENNA (12.0 kWh / 5 h) ---
  Skenaario      Hinta   s/kWh                          Ajat
  Optimi 1h   0.3892 €   3.24   02:00, 03:00, 04:00, 14:00, 15:00
 Optimi 15min  0.3801 €   3.17              Vartti-optimointi
   No Brains   0.4654 €   3.88   22:00, 23:00, 00:00, 01:00, 02:00
--------------------------------------------------
```

---

## Installation

```bash
git clone https://github.com/JussiSavola/tunti-vs-vartti.git
cd tunti-vs-vartti
pip install requests pandas
```

No API key required. No account needed. Spot prices are public.

---

## Usage

### Basic (defaults)

```bash
python tunti-vs-vartti.py
```

Uses: 12 kWh load, 5 hours, day transfer 5.58 s/kWh, night 3.44 s/kWh, margin 0.61 s/kWh.

### With your own parameters

```bash
python tunti-vs-vartti.py \
  --energy 7.4 \      # kWh to charge/consume
  --hours 3 \         # number of hours to use
  --day 6.20 \        # day transfer fee (s/kWh)
  --night 3.80 \      # night transfer fee (s/kWh)
  --margin 0.50       # supplier margin (s/kWh)
```

### Include the No Brains comparison

```bash
python tunti-vs-vartti.py --nobrains
```

Shows savings from smart scheduling vs. a fixed "always charge at night" strategy.

---

## Arguments

| Argument | Short | Default | Description |
|---|---|---|---|
| `--energy` | `-e` | `12.0` | Total energy load in kWh |
| `--hours` | `-o` | `5` | Number of hours to schedule |
| `--day` | `-d` | `5.58` | Day transfer fee in s/kWh (07:00–22:00) |
| `--night` | `-n` | `3.44` | Night transfer fee in s/kWh (22:00–07:00) |
| `--margin` | `-m` | `0.61` | Supplier margin in s/kWh |
| `--nobrains` | | off | Enable No Brains strategy comparison |

> **Transfer fees and margin are in senttiä per kWh (s/kWh).** Check your electricity contract for your actual values.

---

## How pricing is calculated

For each time slot:

```
Total price = Spot price with VAT  +  Transfer fee / 100  +  Margin / 100
```

Transfer fee switches between day and night rate at **07:00** and **22:00**.

Spot prices (with VAT) are fetched directly from [spot-hinta.fi](https://spot-hinta.fi) at both 60-minute and 15-minute resolutions.

---

## The actual question this answers

**Is 15-minute scheduling worth the complexity?**

On a typical day the difference between Optimi 1h and Optimi 15min is small — usually 1–5%. But the "No Brains" comparison is often revealing: blindly scheduling at night can be noticeably more expensive than actually looking at prices, especially on days with low midday solar production or high morning demand.

Run it daily for a month and you'll have your own answer.

---

## Use cases

- **EV charging** — find the cheapest window for your nightly charge
- **Water heater scheduling** — plan electric boiler hours
- **Heat pump pre-heating** — pre-condition before expensive peak hours
- **Research** — understand the actual value of 15-min vs 1-hour price data for your load profile

---

## Data source

Prices fetched from **[spot-hinta.fi](https://spot-hinta.fi)** — a free, no-login Finnish spot price API. Tomorrow's prices become available after ~13:00 EET when Nord Pool publishes the day-ahead market results.

---

## Requirements

- Python 3.8+
- `requests`
- `pandas`

---

## License

GPL-3.0

---

*Made in Finland. Runs on coffee and spite toward high electricity bills.*
