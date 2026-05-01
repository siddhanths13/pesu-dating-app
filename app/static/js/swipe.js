async function swipe(liked) {
  const card = document.getElementById('candidate-card');
  const swipedId = card.dataset.id;
  const formData = new URLSearchParams();
  formData.set('swiped_id', swipedId);
  formData.set('liked', liked ? '1' : '0');

  const response = await fetch('/swipe', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: formData.toString()
  });

  const data = await response.json();
  const status = document.getElementById('status');
  status.innerText = data.match ? "It's a match! 🎉" : 'Swipe saved!';

  setTimeout(() => window.location.reload(), 900);
}
