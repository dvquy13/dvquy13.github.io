-- schema-markup.lua
-- Injects BlogPosting JSON-LD schema into each blog post's <head>.
-- Reads title, date, subtitle/description, categories, keywords from frontmatter.

local SITE_URL = "https://dvquys.com"

local MONTHS = {
  January = "01", February = "02", March = "03", April = "04",
  May = "05", June = "06", July = "07", August = "08",
  September = "09", October = "10", November = "11", December = "12"
}

local function meta_to_string(val)
  if not val then return nil end
  return pandoc.utils.stringify(val)
end

local function json_escape(s)
  if not s then return "" end
  s = s:gsub('\\', '\\\\')
  s = s:gsub('"', '\\"')
  s = s:gsub('\n', '\\n')
  s = s:gsub('\r', '\\r')
  s = s:gsub('\t', '\\t')
  return s
end

local function normalize_date(date_str)
  if not date_str or date_str == "" then return "" end
  -- Already ISO: 2026-01-09
  if date_str:match("^%d%d%d%d%-%d%d%-%d%d$") then
    return date_str
  end
  -- Human-readable: "January 9, 2026"
  local month_name, day, year = date_str:match("^(%a+)%s+(%d+),%s+(%d%d%d%d)$")
  if month_name and MONTHS[month_name] then
    return string.format("%s-%s-%02d", year, MONTHS[month_name], tonumber(day))
  end
  return date_str
end

local function post_url_from_input(input_file)
  -- e.g. /Users/.../posts/the-30m-promise/index.qmd -> posts/the-30m-promise/
  local rel = input_file:match(".+(posts/[^/]+)/index%.qmd$")
  if rel then
    return SITE_URL .. "/" .. rel .. "/"
  end
  return SITE_URL
end

function Meta(meta)
  local title = meta_to_string(meta.title)
  if not title then return meta end

  local date = normalize_date(meta_to_string(meta.date))

  local description = meta_to_string(meta.subtitle) or meta_to_string(meta.description) or ""

  local keywords = ""
  if meta.keywords then
    keywords = meta_to_string(meta.keywords)
  elseif meta.categories then
    keywords = meta_to_string(meta.categories)
  end

  local post_url = SITE_URL
  local ok, input_file = pcall(function() return quarto.doc.input_file end)
  if ok and input_file then
    post_url = post_url_from_input(input_file)
  end

  local json = string.format(
    '{"@context":"https://schema.org","@type":"BlogPosting",' ..
    '"headline":"%s","author":{"@type":"Person","name":"Quy Dinh","url":"%s"},' ..
    '"publisher":{"@type":"Person","name":"Quy Dinh","url":"%s"},' ..
    '"datePublished":"%s","description":"%s","keywords":"%s","url":"%s"}',
    json_escape(title),
    json_escape(SITE_URL),
    json_escape(SITE_URL),
    json_escape(date),
    json_escape(description),
    json_escape(keywords),
    json_escape(post_url)
  )

  local script = '<script type="application/ld+json">\n' .. json .. '\n</script>'

  if not meta['header-includes'] then
    meta['header-includes'] = pandoc.MetaList({})
  end
  table.insert(meta['header-includes'], pandoc.MetaBlocks({
    pandoc.RawBlock('html', script)
  }))

  return meta
end
