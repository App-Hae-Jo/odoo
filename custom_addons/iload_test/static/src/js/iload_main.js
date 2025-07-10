/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.IloadMain = publicWidget.Widget.extend({
    selector: '.oe_structure',
    events: {
        // 'click .some_button': '_onSomeButtonClick',
        // 'change #imageFile': '_onImageFileChange',
    },

    /**
     * @override
     */
    start: function () {
        console.log("Iload main JS loaded!");
        // 여기에 페이지 로드 시 실행될 초기화 로직을 추가합니다.
        // 예: 특정 필드의 값 초기화, 이벤트 리스너 등록 등

        // 예시: 파일 업로드 폼 유효성 검사 (아주 기본적인 예시)
        const uploadForm = this.$('form[action="/iload/ocr_process"]');
        if (uploadForm.length) {
            uploadForm.on('submit', function (event) {
                const imageFile = $(this).find('#imageFile')[0];
                if (!imageFile.files.length) {
                    alert('Please select an image or PDF file to upload.');
                    event.preventDefault(); // 폼 제출 방지
                }
            });
        }

        return this._super.apply(this, arguments);
    },

    // _onSomeButtonClick: function (ev) {
    //     ev.preventDefault();
    //     console.log("Button clicked!");
    //     // 여기에 버튼 클릭 시 실행될 로직을 추가합니다.
    // },

    // _onImageFileChange: function (ev) {
    //     console.log("File selected:", ev.target.files[0].name);
    //     // 파일 선택 시 추가적인 UI 업데이트 또는 유효성 검사 로직
    // },

    /**
     * @override
     */
    destroy: function () {
        console.log("Iload main JS destroyed.");
        // 여기에 페이지를 떠날 때 실행될 정리 로직을 추가합니다.
        this._super.apply(this, arguments);
    },
});