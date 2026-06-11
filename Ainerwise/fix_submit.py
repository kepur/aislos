import re

with open('/Users/mac/Code_Start/Ainerwise/frontend/pages/submit-requirement.vue', 'r') as f:
    content = f.read()

# Top level bg
content = content.replace(
    '<div class="min-h-screen bg-gradient-to-br from-emerald-50 via-cyan-50 to-slate-100">',
    '<div class="min-h-screen pt-10 pb-20">'
)

# Text colors
content = content.replace('text-emerald-700', 'text-primary-400')
content = content.replace('text-slate-950', 'text-white')
content = content.replace('text-slate-900', 'text-white')
content = content.replace('text-slate-600', 'text-slate-300')
content = content.replace('text-slate-500', 'text-slate-400')
content = content.replace('text-slate-700', 'text-slate-300')

# Backgrounds and borders
content = content.replace('bg-white/80', 'glass-panel border-primary-500/30')
content = content.replace('bg-white border p-6', 'glass-panel p-6 border-primary-500/30')
content = content.replace('bg-white border p-5', 'glass-panel p-5 border-white/10')
content = content.replace('bg-white border', 'glass-panel border-primary-500/30')

# Specific amber warning
content = content.replace('bg-amber-50 border border-amber-200', 'bg-amber-500/10 border border-amber-500/30')
content = content.replace('text-amber-900', 'text-amber-200')

# Specific emerald success
content = content.replace('bg-emerald-50 border border-emerald-200', 'bg-emerald-500/10 border border-emerald-500/30')
content = content.replace('text-emerald-900', 'text-emerald-200')
content = content.replace('bg-emerald-500', 'bg-emerald-400')
content = content.replace('bg-emerald-100 text-emerald-800', 'bg-emerald-500/20 text-emerald-300')

# Specific amber active state
content = content.replace('bg-amber-500', 'bg-amber-400')
content = content.replace('bg-amber-100 text-amber-800', 'bg-amber-500/20 text-amber-300')

# Specific slate pending state
content = content.replace('bg-slate-300', 'bg-slate-600')
content = content.replace('bg-slate-100 text-slate-600', 'bg-slate-800 text-slate-400')

# Indigo chat user msgs
content = content.replace('bg-indigo-600 text-white border-indigo-600', 'bg-primary-600 text-white border-primary-500')
content = content.replace('text-indigo-100', 'text-primary-100')
content = content.replace('text-indigo-700', 'text-primary-400')
content = content.replace('bg-indigo-50', 'bg-primary-500/20')

# AI chat msg bg
content = content.replace('bg-white text-slate-700 border-slate-200', 'bg-white/5 text-slate-200 border-white/10')

# Chat scroll area bg
content = content.replace('bg-gradient-to-b from-white to-slate-50', 'bg-transparent')

# Level selection buttons
content = content.replace("bg-white text-slate-700 border-slate-200 hover:border-slate-500", "bg-white/5 text-slate-300 border-white/10 hover:border-white/30")
content = content.replace("bg-slate-950 text-white border-slate-950", "bg-primary-600 text-white border-primary-500")

# Primary 50 panel
content = content.replace('bg-primary-50', 'bg-primary-900/30')
content = content.replace('border-primary-200', 'border-primary-500/30')

with open('/Users/mac/Code_Start/Ainerwise/frontend/pages/submit-requirement.vue', 'w') as f:
    f.write(content)
