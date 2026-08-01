-- pdf_math_filter.lua — map Unicode math symbols in prose to LaTeX math.
-- Str elements only: Code/CodeBlock stay verbatim. Runs of super/subscript
-- digits collapse into a single script group (10⁻⁹ -> {}^{-9}).

local SYM = {
  ["α"]="\\alpha", ["β"]="\\beta", ["γ"]="\\gamma", ["δ"]="\\delta",
  ["λ"]="\\lambda", ["σ"]="\\sigma", ["φ"]="\\varphi", ["χ"]="\\chi",
  ["Σ"]="\\Sigma", ["Δ"]="\\Delta",
  ["≈"]="\\approx", ["→"]="\\to", ["∈"]="\\in", ["≥"]="\\ge", ["≤"]="\\le",
  ["×"]="\\times", ["·"]="\\cdot", ["⊆"]="\\subseteq", ["⊂"]="\\subset",
  ["∧"]="\\wedge", ["≡"]="\\equiv", ["∪"]="\\cup", ["∩"]="\\cap",
  ["∞"]="\\infty", ["±"]="\\pm", ["∝"]="\\propto", ["≠"]="\\ne",
  ["∎"]="\\blacksquare", ["′"]="{}^{\\prime}", ["−"]="-", ["…"]="\\dots",
  ["⊊"]="\\subsetneq", ["⟹"]="\\Longrightarrow", ["⟸"]="\\Longleftarrow",
  ["⟺"]="\\Longleftrightarrow", ["⊔"]="\\sqcup", ["≼"]="\\preceq",
  ["≅"]="\\cong", ["∏"]="\\prod", ["✓"]="\\checkmark", ["⧵"]="\\smallsetminus",
  ["∖"]="\\smallsetminus", ["∅"]="\\varnothing", ["∉"]="\\notin", ["∀"]="\\forall",
  ["∃"]="\\exists", ["⋅"]="\\cdot", ["↦"]="\\mapsto", ["⇒"]="\\Rightarrow",
  ["⇔"]="\\Leftrightarrow", ["∼"]="\\sim", ["≃"]="\\simeq", ["∘"]="\\circ",
}
local SUP = { ["⁰"]="0", ["¹"]="1", ["²"]="2", ["³"]="3", ["⁴"]="4",
  ["⁵"]="5", ["⁶"]="6", ["⁷"]="7", ["⁸"]="8", ["⁹"]="9", ["⁻"]="-" }
local SUB = { ["₀"]="0", ["₁"]="1", ["₂"]="2", ["₃"]="3", ["₄"]="4",
  ["₅"]="5", ["₆"]="6", ["₇"]="7", ["₈"]="8", ["₉"]="9" }

-- Inside $...$ spans the same symbols appear as raw Unicode in math mode;
-- substitute macro names directly (no \( wrapper — already in math).
function Math(el)
  local changed = false
  local t = el.text
  -- unicode-math points \setminus at U+29F5, absent from Latin Modern Math
  if t:find("\\setminus", 1, true) then
    t = t:gsub("\\setminus", "\\smallsetminus"); changed = true
  end
  for ch, macro in pairs(SYM) do
    if t:find(ch, 1, true) then t = t:gsub(ch, macro .. " "); changed = true end
  end
  for ch, d in pairs(SUP) do
    if t:find(ch, 1, true) then t = t:gsub(ch, "^{" .. d .. "}"); changed = true end
  end
  for ch, d in pairs(SUB) do
    if t:find(ch, 1, true) then t = t:gsub(ch, "_{" .. d .. "}"); changed = true end
  end
  if changed then el.text = t; return el end
end

function Str(el)
  local out, plain, has_math = {}, {}, false
  local function flush_plain()
    if #plain > 0 then table.insert(out, pandoc.Str(table.concat(plain))); plain = {} end
  end
  local i, text = 1, el.text
  while i <= #text do
    local len = utf8.offset(text, 2, i) or (#text + 1)
    local ch = text:sub(i, len - 1)
    if SUP[ch] or SUB[ch] then
      local script, digits = (SUP[ch] and "^" or "_"), {}
      local tbl = SUP[ch] and SUP or SUB
      while i <= #text do
        local l2 = utf8.offset(text, 2, i) or (#text + 1)
        local c2 = text:sub(i, l2 - 1)
        if tbl[c2] then table.insert(digits, tbl[c2]); i = l2 else break end
      end
      flush_plain(); has_math = true
      table.insert(out, pandoc.RawInline("tex",
        "\\({}" .. script .. "{" .. table.concat(digits) .. "}\\)"))
    elseif SYM[ch] then
      flush_plain(); has_math = true
      -- absorb a trailing _identifier into the math (δ_x -> \delta_x), so no
      -- literal underscore survives after a converted symbol
      local body, nxt = SYM[ch], len
      if text:sub(nxt, nxt) == "_" then
        -- explicit ASCII ranges: %w is byte-based and can swallow lead bytes
        -- of a following multibyte character
        local ident = text:match("^_([A-Za-z0-9]+)", nxt)
        if ident then
          if #ident == 1 then body = body .. "_" .. ident
          else body = body .. "_{\\mathrm{" .. ident .. "}}" end
          nxt = nxt + 1 + #ident
        end
      end
      table.insert(out, pandoc.RawInline("tex", "\\(" .. body .. "\\)"))
      i = nxt
    else
      table.insert(plain, ch); i = len
    end
  end
  if not has_math then return nil end
  flush_plain()
  return out
end
