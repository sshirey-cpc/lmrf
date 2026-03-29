import re

with open('rendered-site/summer-camps.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_embed = (
    '<div class="sqs-block video-block" style="margin: 20px 0;">'
    '<div class="sqs-block-content">'
    '<div style="position:relative; padding-bottom:56.25%; height:0; overflow:hidden; max-width:100%;">'
    '<iframe src="https://www.youtube.com/embed/l92_Z5_tCVM" '
    'style="position:absolute; top:0; left:0; width:100%; height:100%;" '
    'frameborder="0" allowfullscreen></iframe>'
    '</div></div></div>'
)

# Replace the squarespace video block
html = re.sub(
    r'<div class="sqs-block video-block sqs-block-video"[^>]*>.*?</div></div></div></div></div></div>',
    new_embed,
    html,
    count=1,
    flags=re.DOTALL,
)

with open('rendered-site/summer-camps.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Replaced video embed')
