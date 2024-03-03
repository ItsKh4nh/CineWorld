new autoComplete({
    data: {                              // Nguồn dữ liệu (BẮT BUỘC)
      src: films,
    },
    selector: "#autoComplete",           // Bộ chọn trường nhập (Input)                | (Tùy chọn)
    threshold: 2,                        // Số ký tự tối thiểu để khởi tạo Engine      | (Tùy chọn)
    debounce: 100,                       // Thời gian chờ sau khi gõ để khởi tạoEngine | (Tùy chọn)
    searchEngine: "strict",              // Search Engine Mode                         | (Tùy chọn)
    resultsList: {                       // Danh sách kết quả được render              | (Tùy chọn)
        render: true,
        container: source => {
            source.setAttribute("id", "movie_list");
        },
        destination: document.querySelector("#autoComplete"),
        position: "afterend",
        element: "ul"
    },
    maxResults: 5,                         // Số lượng kết quả được render    | (Tùy chọn)
    highlight: true,                       // Highlight kết quả phù hợp       | (Tùy chọn)
    resultItem: {                          // Mục kết quả được render         | (Tùy chọn)
        content: (data, source) => {
            source.innerHTML = data.match;
        },
        element: "li"
    },
    noResults: () => {                     // Script khi không có kết quả phù hợp | (Tùy chọn)
        const result = document.createElement("li");
        result.setAttribute("class", "no_result");
        result.setAttribute("tabindex", "1");
        result.innerHTML = "No Results";
        document.querySelector("#autoComplete_list").appendChild(result);
    },
    onSelection: feedback => {             // Script khi sự kiện chọn được kích hoạt | (Tùy chọn)
        document.getElementById('autoComplete').value = feedback.selection.value;
    }
});