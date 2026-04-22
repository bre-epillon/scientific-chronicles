---
title: "Redirecting to Today's Personality..."
layout: "redirect"
---
<script>
  // Get current MM-DD
  const now = new Date();
  const monthDay = (now.getMonth() + 1).toString().padStart(2, '0') + 
                   "-" + now.getDate().toString().padStart(2, '0');

  // This assumes you have a JSON index of your scientists
  window.location.href = "/anniversaries/" + monthDay;
</script>