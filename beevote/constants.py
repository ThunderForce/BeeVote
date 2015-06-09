max_image_size = 850*1024 # 850 kb
topic_date_format = "%A   %d %B %Y"
proposal_date_format = "%A   %d %B %Y"
comment_date_format = "%Y/%m/%d %H:%M:%S" # 2015/12/31 23:59:59
proposal_input_date_format = "%d/%m/%Y"
proposal_input_time_format = "%H:%M"
feedback_url = 'https://docs.google.com/forms/d/1qFNWDzBg_g1kCyNajcO32ji6vflfdsEc1MUdC4Dowvk/viewform'
wsgiapplication_config = {}
wsgiapplication_config['webapp2_extras.sessions'] = {
    'secret_key': '20beeVote15',
}
user_image_name = 'user-{user_id}.png'
group_image_name = 'group-{group_id}.png'
topic_image_name = 'topic-{group_id}-{topic_id}.png'