class PageHelper:
    def __init__(self, max_entries, current_page, base_url='?p=', items_per_page=10):
        self.max_entries = max_entries
        self.current_page = current_page
        self.items_per_page = items_per_page
        self.base_url = base_url

    @property
    def items_start(self):
        return (self.current_page - 1) * self.items_per_page

    @property
    def items_end(self):
        return self.current_page * self.items_per_page

    def pages(self):
        q, r = divmod(self.max_entries, self.items_per_page)
        if r != 0:
            q += 1
        return q

    def page_str(self):
        page_str = ''
        page_start = self.current_page - 5
        page_end = self.current_page + 5
        page_min = max(1, page_start)
        page_max = min(page_end, self.pages())
        page_range = range(page_min, page_max+1)
        if page_start <= 1:
            page_range = range(page_min, min(self.pages(), page_min+10+1))
        elif page_end >= self.pages():
            page_range = range(min(page_min, self.pages()-10+1), page_max+1)

        if self.current_page-1 > 0:
            page_str += "<a class='prev' href={0}{1}>{2}</a>".format(self.base_url, self.current_page-1, 'prev')
        else:
            page_str += "<a class='prev' href={0}>{1}</a>".format('javascript:void(0)', 'prev')

        for i in page_range:
            if i == self.current_page:
                page_str += "<a class='current' href={0}{1}>{2}</a>".format(self.base_url, i, i)
            else:
                page_str += "<a href={0}{1}>{2}</a>".format(self.base_url, i, i)
        if self.current_page < self.pages():
            page_str += "<a class='next' href={0}{1}>{2}</a>".format(self.base_url, self.current_page+1, 'next')
        else:
            page_str += "<a class='next' href={0}>{1}</a>".format('javascript:void(0)', 'next')

        return page_str

