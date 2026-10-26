// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

import fs from 'node:fs'
import path from 'node:path'

// allowedRoles chỉ mang tính chất hiển thị và lọc sơ bộ trên giao diện;
// phân quyền truy cập thực tế được gateway kiểm soát theo đường dẫn thư mục lưu trữ:
// - portal/ và guides/public/ (mọi vai trò đọc)
// - guides/technician/ (kỹ thuật viên trở lên đọc)
// - guides/admin/ (chỉ admin đọc)
// - Chỉ quản lý và admin được ghi.
export interface GuideDocument {
  id: string
  title: string
  description: string
  category: 'GENERAL' | 'STUDENT' | 'TECHNICIAN' | 'MANAGER' | 'ADMIN'
  categoryLabel: string
  fileName: string
  filePath: string
  fileSize: string
  fileType: string
  allowedRoles: string[]
  updatedAt: string
  uploadedBy?: string
  content: string
  isCustom?: boolean
}

export interface CampusUnit {
  id: string
  code: string
  name: string
  location: string
  hotline: string
  email: string
  scope: string
  manager: string
  technicians: string[]
}

export interface RoleGroup {
  id: string
  role: string
  roleLabel: string
  name: string
  description: string
  duties: string[]
  workflowPermissions: string[]
}

export const MANIFEST_FILE_PATH = 'portal/manifest.json'

export function getMetaFilePath(filePath: string): string {
  return `${filePath}.meta.json`
}

export function getGuideDirectory(category: string): string {
  if (category === 'ADMIN') return 'guides/admin'
  if (category === 'TECHNICIAN' || category === 'MANAGER') return 'guides/technician'
  return 'guides/public'
}

class AsyncMutex {
  private queue = Promise.resolve()

  async runExclusive<T>(task: () => Promise<T>): Promise<T> {
    const next = this.queue.then(() => task())
    this.queue = next.then(() => {}, () => {})
    return next
  }
}

export const manifestLock = new AsyncMutex()

let campusFileWarned = false

// PORTAL_DATA_DIR chỉ thư mục chứa campuses.json, cần khi chạy bản build ngoài repo;
// không đặt thì dò theo thư mục hiện tại như lúc chạy `npm run dev` trong app/
function campusFileCandidates(): string[] {
  const dir = process.env.PORTAL_DATA_DIR
  if (dir) return [path.resolve(dir, 'campuses.json')]
  return [
    path.resolve(process.cwd(), '../data/samples/campuses.json'),
    path.resolve(process.cwd(), 'data/samples/campuses.json'),
    '/data/samples/campuses.json',
  ]
}

function loadCampusAddresses(): Record<string, string> {
  const possiblePaths = campusFileCandidates()
  for (const p of possiblePaths) {
    try {
      if (fs.existsSync(p)) {
        const raw = fs.readFileSync(p, 'utf-8')
        const data = JSON.parse(raw) as { campuses?: Array<{ code: string, address: string }> }
        const map: Record<string, string> = {}
        for (const c of data.campuses ?? []) {
          if (c.code && c.address) {
            map[c.code] = c.address
          }
        }
        return map
      }
    }
    catch (err) {
      console.warn(`Lỗi đọc ${p}:`, (err as Error).message)
    }
  }
  if (!campusFileWarned) {
    campusFileWarned = true
    console.warn('Không đọc được campuses.json, portal không hiện địa chỉ cơ sở. Đã thử:',
      possiblePaths.join(', '), '- đặt PORTAL_DATA_DIR')
  }
  return {}
}

export function getCampusUnits(): CampusUnit[] {
  const addresses = loadCampusAddresses()
  return [
    {
      id: 'unit-cs1',
      code: 'CS1',
      name: 'Tổ Kỹ thuật & Quản lý Phòng Lab Cơ sở 1',
      location: addresses.CS1 || 'Số 298 Đường Cầu Diễn, Phường Tây Tựu, Thành phố Hà Nội',
      hotline: 'Liên hệ Phòng Quản trị Thiết bị (CS1)',
      email: 'hotro-cs1@dxlab.local',
      scope: 'Quản lý, bảo trì hệ thống phòng thực hành máy tính Khu A, Khu B và hạ tầng mạng campus CS1',
      manager: 'Trưởng Phòng Lab CS1 (truongphong@dxlab.local)',
      technicians: ['Kỹ thuật Viên CS1 (kythuatvien@dxlab.local)'],
    },
    {
      id: 'unit-cs2',
      code: 'CS2',
      name: 'Tổ Hỗ trợ Kỹ thuật & Sửa chữa Thiết bị Cơ sở 2',
      location: addresses.CS2 || 'Phường Tây Tựu, Thành phố Hà Nội',
      hotline: 'Liên hệ Phòng Quản trị Thiết bị (CS2)',
      email: 'hotro-cs2@dxlab.local',
      scope: 'Quản lý thiết bị CNTT các phòng máy thực hành khoa CNTT & Ngoại ngữ tại CS2',
      manager: 'Trưởng Phòng Lab CS2 (truongphong_cs2@dxlab.local)',
      technicians: ['Kỹ thuật Viên CS2 (kythuatvien_cs2@dxlab.local)'],
    },
    {
      id: 'unit-cs3',
      code: 'CS3',
      name: 'Tổ Hỗ trợ Kỹ thuật & Khảo thí Cơ sở 3',
      location: addresses.CS3 || 'Phường Phù Vân, Tỉnh Ninh Bình',
      hotline: 'Liên hệ Phòng Quản trị Thiết bị (CS3)',
      email: 'hotro-cs3@dxlab.local',
      scope: 'Phòng thực hành tin học cơ sở và trung tâm khảo thí phòng máy CS3',
      manager: 'Trưởng Phòng Lab CS3 (truongphong_cs3@dxlab.local)',
      technicians: ['Kỹ thuật Viên CS3 (kythuatvien_cs3@dxlab.local)'],
    },
  ]
}

export const CAMPUS_UNITS: CampusUnit[] = getCampusUnits()

export const ROLE_GROUPS: RoleGroup[] = [
  {
    id: 'role-student',
    role: 'ROLE_STUDENT',
    roleLabel: 'Sinh viên / Giảng viên',
    name: 'Khối Người dùng Phòng máy & Thiết bị',
    description: 'Người dùng trực tiếp sử dụng thiết bị CNTT tại các phòng thực hành, lớp học thông minh và trung tâm dữ liệu HaUI.',
    duties: [
      'Bảo quản thiết bị máy tính, màn hình, phụ kiện trong suốt buổi học.',
      'Gửi yêu cầu báo hỏng (kèm ảnh chụp sự cố) ngay khi phát hiện hỏng hóc.',
      'Theo dõi tiến độ sửa chữa của phiếu báo hỏng do mình tạo.',
      'Xác nhận kết quả xử lý thiết bị sau khi hoàn thành.',
    ],
    workflowPermissions: [
      'Tạo ticket báo hỏng (DRAFT -> SUBMITTED)',
      'Xem danh sách ticket cá nhân',
      'Xem tài liệu hướng dẫn báo hỏng và nội quy phòng máy',
    ],
  },
  {
    id: 'role-technician',
    role: 'ROLE_TECHNICIAN',
    roleLabel: 'Kỹ thuật viên',
    name: 'Tổ Kỹ thuật Sửa chữa & Bảo trì',
    description: 'Chuyên viên kỹ thuật trực tiếp chẩn đoán lỗi phần cứng, phần mềm, xử lý mạng và cập nhật hệ thống tài sản.',
    duties: [
      'Tiếp nhận ticket phân công thuộc cơ sở làm việc.',
      'Kiểm tra thực tế hiện trường, chẩn đoán sự cố phần cứng/mạng.',
      'Sửa chữa, thay thế linh kiện và cài đặt lại hệ điều hành/môi trường.',
      'Lập biên bản xử lý, đồng bộ trạng thái thiết bị về hệ thống tài sản Snipe-IT.',
    ],
    workflowPermissions: [
      'Nhận việc và chuyển trạng thái xử lý (ASSIGNED -> IN_PROGRESS)',
      'Lập giải pháp và hoàn thành sửa chữa (IN_PROGRESS -> RESOLVED)',
      'Xem hàng đợi ticket theo cơ sở (co_so)',
      'Tải lên và quản lý tài liệu kỹ thuật',
    ],
  },
  {
    id: 'role-manager',
    role: 'ROLE_LAB_MANAGER',
    roleLabel: 'Trưởng phòng Lab',
    name: 'Ban Quản lý Phòng thí nghiệm & Nghiệm thu',
    description: 'Cán bộ quản lý chịu trách nhiệm điều phối kỹ thuật, bảo đảm SLA và nghiệm thu chất lượng sửa chữa theo từng cơ sở.',
    duties: [
      'Duyệt tiếp nhận hoặc từ chối phiếu báo hỏng không hợp lệ.',
      'Phân công kỹ thuật viên phụ trách sửa chữa theo cơ sở.',
      'Nghiệm thu kết quả sửa chữa, đóng ticket hoặc yêu cầu làm lại (reopen).',
      'Theo dõi tiến độ, số lượng ticket và báo cáo dashboard cơ sở.',
    ],
    workflowPermissions: [
      'Tiếp nhận và phân công (SUBMITTED -> ASSIGNED)',
      'Từ chối ticket kèm lý do (SUBMITTED -> REJECTED)',
      'Nghiệm thu đóng ticket (RESOLVED -> CLOSED)',
      'Mở lại ticket nếu chưa đạt (RESOLVED -> IN_PROGRESS)',
      'Xem báo cáo thống kê dashboard cơ sở',
    ],
  },
  {
    id: 'role-admin',
    role: 'ROLE_ADMIN',
    roleLabel: 'Quản trị hệ thống',
    name: 'Ban Quản trị Nền tảng DX-OS',
    description: 'Quản trị viên toàn quyền cấu hình Open-Core, API Gateway, tài khoản Keycloak, quy trình BPMN và lưu trữ SeaweedFS.',
    duties: [
      'Giám sát hoạt động của API Gateway APISIX, Keycloak SSO và Flowable.',
      'Quản lý danh mục tài sản, cấu hình tham số hệ thống và phân quyền.',
      'Kiểm tra tính nhất quán dữ liệu giữa Data API, Flowable và Snipe-IT.',
      'Sao lưu định kỳ cơ sở dữ liệu PostgreSQL và phân vùng lưu trữ SeaweedFS.',
    ],
    workflowPermissions: [
      'Toàn quyền quản trị luồng và ticket trên toàn bộ 3 cơ sở',
      'Quản lý danh sách quy trình BPMN Flowable',
      'Quản trị tài liệu hệ thống và cấu hình gateway',
    ],
  },
]

export const DEFAULT_GUIDES: GuideDocument[] = [
  {
    id: 'guide-01',
    title: 'Hướng dẫn Báo hỏng Thiết bị CNTT Phòng máy',
    description: 'Quy trình các bước báo sự cố máy tính, thiết bị mạng phòng lab và theo dõi trạng thái xử lý qua DX-Helpdesk.',
    category: 'STUDENT',
    categoryLabel: 'Hướng dẫn Sinh viên',
    fileName: 'huong-dan-bao-hong-thiet-bi.md',
    filePath: 'guides/public/huong-dan-bao-hong-thiet-bi.md',
    fileSize: '1.8 KB',
    fileType: 'markdown',
    allowedRoles: ['ROLE_STUDENT', 'ROLE_TECHNICIAN', 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'],
    updatedAt: '2026-10-18',
    uploadedBy: 'Ban Quản trị DX-Lab',
    content: `# Hướng dẫn Báo hỏng Thiết bị CNTT – HaUI

## 1. Mục đích
Tài liệu hướng dẫn sinh viên, giảng viên và cán bộ tại Đại học Công nghiệp Hà Nội (HaUI) cách tạo yêu cầu báo hỏng thiết bị CNTT (máy tính, màn hình, bàn phím, chuột, thiết bị mạng, máy in) tại các phòng thực hành thuộc 3 cơ sở đào tạo.

## 2. Các bước thực hiện
1. **Đăng nhập hệ thống**: Sử dụng tài khoản HaUI SSO để đăng nhập vào DX-Helpdesk.
2. **Chọn thiết bị**: Chọn thiết bị được giao hoặc tra cứu thiết bị phòng lab qua mã tài sản (Asset Tag).
3. **Mô tả sự cố**:
   - Chọn loại sự cố: Phần cứng, Phần mềm / Môi trường, Mạng / Tài khoản, Tài sản phòng lab.
   - Nhập tiêu đề và mô tả chi tiết biểu hiện lỗi.
   - Đính kèm ảnh chụp sự cố (nếu có) để kỹ thuật viên nắm rõ hiện trạng.
4. **Hệ thống AI gợi ý**: Nền tảng sẽ tự động gợi ý phân loại và mức độ ưu tiên để người dùng xác nhận hoặc chỉnh sửa trước khi gửi.
5. **Theo dõi tiến độ**: Sau khi gửi, phiếu báo hỏng được định tuyến tự động về tổ kỹ thuật phụ trách cơ sở tương ứng (CS1, CS2, CS3).

## 3. Quy định thời gian phản hồi (SLA)
- **Mức Khẩn cấp (URGENT)**: Phản hồi trong vòng 15 - 30 phút.
- **Mức Cao (HIGH)**: Phản hồi trong vòng 2 giờ làm việc.
- **Mức Trung bình (MEDIUM)**: Phản hồi trong vòng 8 giờ làm việc.
- **Mức Thấp (LOW)**: Phản hồi trong vòng 24 giờ làm việc.

## 4. Hỗ trợ khẩn cấp
Nếu sự cố ảnh hưởng trực tiếp đến giờ thi hoặc buổi thực hành đang diễn ra, vui lòng liên hệ phòng quản trị thiết bị tại cơ sở tương ứng.
`,
  },
  {
    id: 'guide-02',
    title: 'Nội quy và Quy định Sử dụng Phòng Thực hành Máy tính',
    description: 'Quy tắc an toàn, trách nhiệm bảo quản tài sản công và xử lý sự cố thiết bị tại 3 cơ sở đào tạo HaUI.',
    category: 'GENERAL',
    categoryLabel: 'Nội quy Chung',
    fileName: 'noi-quy-phong-may-thuc-hanh.md',
    filePath: 'guides/public/noi-quy-phong-may-thuc-hanh.md',
    fileSize: '1.4 KB',
    fileType: 'markdown',
    allowedRoles: ['ROLE_STUDENT', 'ROLE_TECHNICIAN', 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'],
    updatedAt: '2026-10-18',
    uploadedBy: 'Ban Quản lý Phòng Lab',
    content: `# Nội quy Phòng Thực hành Máy tính – HaUI

## 1. Quy định chung
- Mọi cá nhân khi vào phòng thực hành máy tính phải xuất trình thẻ sinh viên / thẻ cán bộ khi có yêu cầu.
- Giữ gìn vệ sinh chung, không mang đồ ăn, thức uống (ngoại trừ nước lọc đóng chai) vào khu vực máy tính.
- Tuyệt đối tuân thủ hướng dẫn của cán bộ quản lý phòng lab và kỹ thuật viên trực phòng máy.

## 2. Sử dụng thiết bị
- Kiểm tra tình trạng thiết bị trước khi bắt đầu buổi thực hành. Nếu phát hiện hư hỏng, báo ngay cho kỹ thuật viên trực hoặc gửi yêu cầu trên DX-Helpdesk.
- Không tự ý tháo dỡ, hoán đổi linh kiện (bàn phím, chuột, RAM, dây cáp mạng) giữa các máy tính.
- Không tự ý cài đặt phần mềm độc hại, phần mềm can thiệp hệ thống hoặc thay đổi cấu hình mạng LAN.
- Khi kết thúc buổi học, tắt máy tính đúng quy trình, kê lại ghế và dọn dẹp khu vực ngồi.

## 3. Xử lý vi phạm
- Các hành vi cố ý phá hoại tài sản công, tự ý di dời thiết bị ra khỏi phòng thực hành sẽ bị lập biên bản, xử lý kỷ luật theo quy chế nhà trường và bồi thường thiệt hại theo quy định.
`,
  },
  {
    id: 'guide-03',
    title: 'Quy trình Tiếp nhận và Xử lý Sự cố Kỹ thuật',
    description: 'Hướng dẫn kỹ thuật viên các bước chẩn đoán, sửa chữa thiết bị, lập biên bản và đồng bộ trạng thái tài sản về Snipe-IT.',
    category: 'TECHNICIAN',
    categoryLabel: 'Kỹ thuật viên',
    fileName: 'quy-trinh-tiep-nhan-ky-thuat.md',
    filePath: 'guides/technician/quy-trinh-tiep-nhan-ky-thuat.md',
    fileSize: '1.7 KB',
    fileType: 'markdown',
    allowedRoles: ['ROLE_TECHNICIAN', 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'],
    updatedAt: '2026-10-18',
    uploadedBy: 'Đội Kỹ thuật HaUI',
    content: `# Quy trình Tiếp nhận và Xử lý Sự cố (Dành cho Kỹ thuật viên)

## 1. Phạm vi áp dụng
Áp dụng cho kỹ thuật viên thuộc Tổ Kỹ thuật Hỗ trợ tại Cơ sở 1, Cơ sở 2 và Cơ sở 3 của HaUI.

## 2. Quy trình xử lý (BPMN Flowable)
1. **Tiếp nhận ticket**:
   - Nhận thông báo ticket được phân công từ Trưởng phòng lab hoặc tự nhận trong hàng đợi cơ sở.
   - Kiểm tra thông tin thiết bị từ hệ thống quản lý tài sản (Snipe-IT).
2. **Chuyển trạng thái**:
   - Chuyển ticket sang trạng thái \`IN_PROGRESS\` khi bắt đầu thực hiện kiểm tra thực tế.
3. **Chẩn đoán và Sửa chữa**:
   - Tiến hành kiểm tra phần cứng, hệ điều hành, driver hoặc kết nối mạng.
   - Nếu cần thay thế linh kiện, lập đề xuất linh kiện gửi Trưởng phòng lab phê duyệt.
4. **Lập biên bản xử lý & Đồng bộ Snipe-IT**:
   - Ghi rõ tóm tắt nguyên nhân và phương án khắc phục (Resolution Summary).
   - Chuyển trạng thái ticket sang \`RESOLVED\`.
   - Hệ thống tự động đồng bộ trạng thái thiết bị về Snipe-IT (\`Ready to Deploy\` hoặc \`Defective\`).
`,
  },
  {
    id: 'guide-04',
    title: 'Sổ tay Khắc phục Sự cố Máy tính Phòng Lab',
    description: 'Tổng hợp giải pháp khắc phục các lỗi phần cứng, RAM, nguồn, card mạng và hệ điều hành máy trạm phòng thực hành.',
    category: 'TECHNICIAN',
    categoryLabel: 'Kỹ thuật viên',
    fileName: 'so-tay-khac-phuc-su-co-pc.md',
    filePath: 'guides/technician/so-tay-khac-phuc-su-co-pc.md',
    fileSize: '1.6 KB',
    fileType: 'markdown',
    allowedRoles: ['ROLE_TECHNICIAN', 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'],
    updatedAt: '2026-10-18',
    uploadedBy: 'Đội Kỹ thuật HaUI',
    content: `# Sổ tay Khắc phục Sự cố Máy tính Phòng Lab

## 1. Sự cố nguồn và khởi động
- **Máy không lên nguồn**: Kiểm tra ổ cắm, dây nguồn, công tắc nguồn phụ trên PSU, kiểm tra đo điện áp nguồn 12V/5V.
- **Máy bật lên rồi tắt ngay**: Kiểm tra keo tản nhiệt CPU, quạt tản nhiệt, chân cắm RAM bị bám bụi hoặc lỏng.

## 2. Sự cố bộ nhớ RAM
- **Máy kêu bip liên tục (Award/AMI BIOS)**: Tháo thanh RAM, dùng gôm cao su vệ sinh chân tiếp xúc màu vàng kim, lắp lại chặt vào khe RAM.
- **Màn hình xanh BSOD (Memory Management)**: Chạy công cụ chẩn đoán Windows Memory Diagnostic hoặc MemTest86 để phát hiện chip nhớ lỗi.

## 3. Sự cố mạng và kết nối
- **Biểu tượng mạng có dấu chấm than vàng**: Kiểm tra IP DHCP từ router phòng lab, chạy lệnh \`ipconfig /release\` và \`ipconfig /renew\`.
- **Không nhận cáp mạng**: Kiểm tra đầu bấm RJ45, dùng máy test mạng kiểm tra thứ tự 8 sợi dây cáp.
`,
  },
  {
    id: 'guide-05',
    title: 'Quy trình Phân công Công việc và Nghiệm thu',
    description: 'Hướng dẫn Trưởng phòng Lab điều phối kỹ thuật viên theo cơ sở, giám sát SLA, nghiệm thu hoặc yêu cầu mở lại ticket.',
    category: 'MANAGER',
    categoryLabel: 'Trưởng phòng Lab',
    fileName: 'quy-trinh-phan-cong-nghiem-thu.md',
    filePath: 'guides/technician/quy-trinh-phan-cong-nghiem-thu.md',
    fileSize: '1.5 KB',
    fileType: 'markdown',
    allowedRoles: ['ROLE_LAB_MANAGER', 'ROLE_ADMIN'],
    updatedAt: '2026-10-18',
    uploadedBy: 'Ban Quản lý Phòng Lab',
    content: `# Quy trình Phân công Công việc và Nghiệm thu (Trưởng phòng Lab)

## 1. Vai trò của Trưởng phòng Lab
Trưởng phòng Lab (\`ROLE_LAB_MANAGER\`) chịu trách nhiệm quản lý, điều phối công việc sửa chữa thiết bị tại cơ sở được phân công (\`co_so\`), bảo đảm chất lượng và thời gian xử lý sự cố.

## 2. Tiếp nhận và Phân công
- Xem danh sách ticket mới gửi (\`SUBMITTED\`) thuộc cơ sở phụ trách.
- Đánh giá tính chất sự cố và năng lực kỹ thuật viên trực ca để phân công (\`ASSIGNED\`).
- Từ chối tiếp nhận (\`REJECTED\`) kèm lý do rõ ràng nếu thông tin báo hỏng không hợp lệ hoặc thiết bị không thuộc thẩm quyền quản lý.

## 3. Nghiệm thu và Đóng ticket
- Khi kỹ thuật viên hoàn thành và chuyển sang \`RESOLVED\`, Trưởng phòng kiểm tra biên bản xử lý và tình trạng thực tế của thiết bị.
- **Nghiệm thu đạt**: Phê duyệt nghiệm thu, đóng ticket (\`CLOSED\`), xác nhận cập nhật trạng thái tài sản trên Snipe-IT.
- **Nghiệm thu không đạt (Reopen)**: Mở lại ticket về trạng thái \`IN_PROGRESS\`, giao lại cho kỹ thuật viên xử lý bổ sung kèm lý do yêu cầu khắc phục tiếp.
`,
  },
  {
    id: 'guide-06',
    title: 'Tài liệu Vận hành Nền tảng DX-OS Open-Core',
    description: 'Kiến trúc Open-Core, quản lý cấu hình API Gateway APISIX, đồng bộ Keycloak realm, lưu trữ SeaweedFS và BPMN Flowable.',
    category: 'ADMIN',
    categoryLabel: 'Quản trị viên',
    fileName: 'huong-dan-van-hanh-he-thong-dxos.md',
    filePath: 'guides/admin/huong-dan-van-hanh-he-thong-dxos.md',
    fileSize: '2.0 KB',
    fileType: 'markdown',
    allowedRoles: ['ROLE_ADMIN'],
    updatedAt: '2026-10-18',
    uploadedBy: 'Ban Quản trị DX-OS',
    content: `# Tài liệu Vận hành Nền tảng DX-OS Open-Core (Quản trị viên)

## 1. Tổng quan Kiến trúc
- **Tầng 1 (Open-Core Headless)**:
  - Apache APISIX: Gateway API trung tâm, xác thực JWT OIDC qua JWKS, phân quyền \`dxlab-roles\`.
  - Keycloak: Quản lý danh tính, Single Sign-On (SSO), thuộc tính người dùng \`co_so\`.
  - PostgreSQL 18: Lưu trữ CSDL nghiệp vụ (\`dxdata\`), BPMN (\`flowable\`), danh tính (\`keycloak\`).
  - SeaweedFS: Lưu trữ tệp phân tán, bucket \`documents\` qua route \`/api/files\`.
  - Flowable REST: Quản lý và thực thi quy trình nghiệp vụ BPMN 2.0.
- **Tầng 2 (Không gian H-P-D-I)**:
  - H: Con người số, Portal tối giản, nhóm và hồ sơ.
  - P: Quy trình sửa chữa thiết bị.
  - D: Data API FastAPI, dữ liệu mẫu, thống kê dashboard.
  - I: Dịch vụ phân loại AI (scikit-learn) và luật từ khóa dự phòng.
- **Tầng 3 (Ứng dụng Nuxt 4)**:
  - DX-Helpdesk BFF, proxy \`/gw/api/**\` với cookie phiên an toàn.

## 2. Giám sát và Vận hành
- Kiểm tra tính sẵn sàng của hệ thống: \`make smoke\`.
- Quản lý nhật ký hoạt động: \`docker compose logs -f <service_name>\`.
- Khởi động lại hệ thống: \`make down && make up\`.
`,
  },
]
